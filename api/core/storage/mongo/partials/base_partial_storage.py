import logging
from abc import ABC
from collections.abc import AsyncIterator, Callable, Iterable
from contextlib import contextmanager
from typing import Any, Generic, TypeVar, Union

from bson import ObjectId
from bson.errors import InvalidId
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError
from pymongo.results import BulkWriteResult, DeleteResult, InsertManyResult, UpdateResult

from core.domain.errors import DuplicateValueError
from core.storage import ObjectNotFoundException, TenantTuple
from core.storage.mongo.models.base_document import BaseDocumentWithID, BaseDocumentWithStrID
from core.storage.mongo.mongo_types import AsyncCollection, UpdateType
from core.storage.mongo.utils import dump_model, projection

# TODO: we should create a partial storage class for docs that don't use object ids
_D = TypeVar("_D", bound=Union[BaseDocumentWithStrID, BaseDocumentWithID])

_T = TypeVar("_T")


class PartialStorage(ABC, Generic[_D]):
    def __init__(self, tenant: TenantTuple, collection: AsyncCollection, document_type: type[_D]):
        self._tenant, self._tenant_uid = tenant
        self._collection = collection
        self._document_type = document_type
        self._logger = logging.getLogger(self.__class__.__name__)

    @property
    def _object_type(self) -> str:
        return self._document_type.__name__

    @property
    def timeout_ms(self) -> int:
        return 10_000

    @contextmanager
    def _wrap_errors(self):
        try:
            yield
        except DuplicateKeyError as e:
            raise DuplicateValueError(str(e))

    @property
    def tenant(self) -> str:
        return self._tenant

    def _before_update(self, update: UpdateType) -> UpdateType:
        return update

    def _id_filter(self, id: str) -> dict[str, Any]:
        try:
            return {"_id": ObjectId(id)}
        except InvalidId:
            raise AssertionError(f"Invalid benchmark id: {id}")

    def _tenant_filter(self, filter: dict[str, Any]) -> dict[str, Any]:
        return {**filter, "tenant": self._tenant}

    async def _insert_one(self, doc: _D) -> _D:
        doc.tenant = self._tenant
        doc.tenant_uid = self._tenant_uid
        with self._wrap_errors():
            res = await self._collection.insert_one(dump_model(doc))
            doc.id = res.inserted_id
        return doc

    async def insert_many(self, obj: Iterable[_D], ordered: bool = True) -> InsertManyResult:
        dumped: list[dict[str, Any]] = []
        for doc in obj:
            doc.tenant = self._tenant
            dumped.append(dump_model(doc))

        return await self._collection.insert_many(dumped, ordered=ordered)

    async def _find_one_doc(
        self,
        filter: dict[str, Any],
        projection: dict[str, Any] | None = None,
        sort: list[tuple[str, int]] | None = None,
        hint: str | None = None,
    ):
        doc = await self._collection.find_one(self._tenant_filter(filter), projection=projection, sort=sort, hint=hint)
        if doc is None:
            raise ObjectNotFoundException(object_type=self._object_type)
        return doc

    async def _find_one(
        self,
        filter: dict[str, Any],
        projection: dict[str, Any] | None = None,
        sort: list[tuple[str, int]] | None = None,
        hint: str | None = None,
    ) -> _D:
        doc = await self._find_one_doc(filter, projection, sort, hint)
        return self._document_type.model_validate(doc)

    async def _find(
        self,
        filter: dict[str, Any],
        projection: dict[str, Any] | None = None,
        limit: int | None = None,
        skip: int | None = None,
        sort: list[tuple[str, int]] | None = None,
        hint: str | None = None,
        timeout_ms: int | None = None,
    ) -> AsyncIterator[_D]:
        cursor = self._collection.find(self._tenant_filter(filter), projection=projection)
        if limit:
            cursor = cursor.limit(limit)
        if skip:
            cursor = cursor.skip(skip)
        if sort:
            cursor = cursor.sort(sort)
        if hint:
            cursor = cursor.hint(hint)
        ts = timeout_ms or self.timeout_ms
        if ts:
            cursor = cursor.max_time_ms(ts)
        async for doc in cursor:
            try:
                yield self._document_type.model_validate(doc)
            except ValidationError:
                # Failing silently to avoid breaking the whole query
                self._logger.exception(
                    "Error validating document",
                    extra={"document": doc},
                )
                continue

    async def _update_one(
        self,
        filter: dict[str, Any],
        update: UpdateType,
        upsert: bool = False,
        array_filters: list[dict[str, Any]] | None = None,
        throw_on_not_found: bool = True,
        hint: str | None = None,
    ) -> UpdateResult:
        with self._wrap_errors():
            res = await self._collection.update_one(
                self._tenant_filter(filter),
                self._before_update(update),
                upsert=upsert,
                array_filters=array_filters,
                hint=hint,
            )

        if res.matched_count == 0 and throw_on_not_found and not upsert:
            raise ObjectNotFoundException()
        return res

    async def _find_one_and_update_without_tenant(
        self,
        filter: dict[str, Any],
        update: UpdateType,
        projection: dict[str, Any] | None = None,
        return_document: bool = False,
        upsert: bool = False,
        array_filters: list[dict[str, Any]] | None = None,
    ) -> _D:
        try:
            res = await self._collection.find_one_and_update(
                filter,
                self._before_update(update),
                projection=projection,
                return_document=return_document,
                upsert=upsert,
                array_filters=array_filters,
            )
        except DuplicateKeyError as e:
            raise DuplicateValueError(str(e))
        if res is None:
            raise ObjectNotFoundException()
        return self._document_type.model_validate(res)

    async def _find_one_and_update(
        self,
        filter: dict[str, Any],
        update: UpdateType,
        projection: dict[str, Any] | None = None,
        # True for after, False for before
        return_document: bool = False,
        upsert: bool = False,
        array_filters: list[dict[str, Any]] | None = None,
        hint: str | None = None,
    ) -> _D:
        try:
            res = await self._collection.find_one_and_update(
                self._tenant_filter(filter),
                self._before_update(update),
                projection=projection,
                return_document=return_document,
                upsert=upsert,
                array_filters=array_filters,
            )
        except DuplicateKeyError as e:
            raise DuplicateValueError(str(e))
        if res is None:
            raise ObjectNotFoundException()
        return self._document_type.model_validate(res)

    async def _update_one_and_return(
        self,
        filter: dict[str, Any],
        update: UpdateType,
        include: Iterable[str] | None = None,
        # True by default
        return_document: bool = True,
        upsert: bool = False,
        array_filters: list[dict[str, Any]] | None = None,
    ) -> _D | None:
        """Update a document and return the updated document if include is provided"""
        if include is not None:
            return await self._find_one_and_update(
                filter,
                update,
                projection=projection(include=include),
                return_document=return_document,
                upsert=upsert,
                array_filters=array_filters,
            )
        await self._update_one(filter, update, upsert=upsert, array_filters=array_filters, throw_on_not_found=True)
        return None

    async def _update_many(
        self,
        filter: dict[str, Any],
        update: UpdateType,
        array_filters: list[dict[str, Any]] | None = None,
        hint: str | None = None,
    ) -> UpdateResult:
        return await self._collection.update_many(
            self._tenant_filter(filter),
            self._before_update(update),
            array_filters=array_filters,
            hint=hint,
        )

    async def _delete_one(
        self,
        filter: dict[str, Any],
        throw_on_not_found: bool = True,
    ) -> DeleteResult:
        res = await self._collection.delete_one(self._tenant_filter(filter))
        if throw_on_not_found and res.deleted_count != 1:
            raise ObjectNotFoundException(
                "Agent evaluator not found",
                code="evaluator_not_found",
                extra={"filter": filter},
            )
        return res

    async def _count(self, filter: dict[str, Any], max_time_ms: int | None = None) -> int:
        return await self._collection.count_documents(self._tenant_filter(filter), maxTimeMS=max_time_ms or 0)

    async def bulk_write(self, operations: list[Any]) -> BulkWriteResult:
        return await self._collection.bulk_write(operations)

    async def _distinct(self, key: str, filter: dict[str, Any], hint: str | None = None) -> set[Any]:
        # TODO: mongo db 7 does not support hints for distinct
        return set(await self._collection.distinct(key, self._tenant_filter(filter)))

    async def _aggregate(
        self,
        pipeline: list[dict[str, Any]],
        timeout_ms: int = 0,
        map_fn: Callable[[dict[str, Any]], _T] = lambda x: x,
        **kwargs: Any,
    ) -> AsyncIterator[_T]:
        if "$match" in pipeline[0]:
            pipeline[0]["$match"]["tenant"] = self._tenant
        cursor = self._collection.aggregate(pipeline, maxTimeMS=timeout_ms or self.timeout_ms, **kwargs)
        async for doc in cursor:
            try:
                yield map_fn(doc)
            except ValidationError:
                # Failing silently to avoid breaking the whole query
                self._logger.exception(
                    "Error validating document",
                    extra={"document": doc},
                )
                continue
