# Mongo Docs:https://pymongo.readthedocs.io/en/stable/api/pymongo/collection.html
# This stub file is incomplete and only contains the methods that are used in the project.
from collections.abc import Sequence
from typing import Any, AsyncIterator, NotRequired, Optional, Protocol, TypedDict, Union

from pymongo.client_session import ClientSession
from pymongo.results import BulkWriteResult, DeleteResult, InsertManyResult, InsertOneResult, UpdateResult

UpdateType = Union[dict[str, Any], list[dict[str, Any]]]


class AsyncCollection(Protocol):
    """
    A type definition for the AsyncCollection class from the motor library.
    """

    @property
    def name(self) -> str: ...

    async def insert_one(self, obj: dict[str, Any]) -> InsertOneResult: ...

    async def insert_many(self, obj: list[dict[str, Any]], ordered: bool = True) -> InsertManyResult: ...

    async def find_one(
        self,
        filter: dict[str, Any],
        projection: Optional[dict[str, Any]] = None,
        sort: list[tuple[str, int]] | None = None,
        hint: str | None = None,
    ) -> dict[str, Any] | None: ...

    def find(
        self,
        filter: dict[str, Any],
        projection: Optional[dict[str, Any]] = None,
    ) -> "AsyncCursor": ...

    async def delete_one(self, filter: dict[str, Any]) -> DeleteResult: ...

    async def delete_many(self, filter: dict[str, Any]) -> DeleteResult: ...

    async def update_one(
        self,
        filter: dict[str, Any],
        update: UpdateType,
        upsert: bool = False,
        array_filters: Optional[list[dict[str, Any]]] = None,
        hint: str | None = None,
    ) -> UpdateResult: ...

    async def replace_one(
        self,
        filter: dict[str, Any],
        update: UpdateType,
        upsert: bool = False,
    ) -> UpdateResult: ...

    async def update_many(
        self,
        filter: dict[str, Any],
        update: UpdateType,
        array_filters: list[dict[str, Any]] | None = None,
        hint: str | None = None,
    ) -> UpdateResult: ...

    def aggregate(
        self,
        pipeline: list[dict[str, Any]],
        maxTimeMS: int | None = None,
        **kwargs: Any,
    ) -> "AsyncCursor": ...

    async def count_documents(
        self,
        filter: dict[str, Any],
        hint: str | None = None,
        maxTimeMS: int | None = None,
    ) -> int: ...

    async def drop_index(self, index_or_name: str) -> None: ...

    async def drop_indexes(self) -> None: ...

    async def create_index(
        self,
        index: Union[str, list[tuple[str, Any]]],
        session: ClientSession | None = None,
        comment: Any = None,
        name: Optional[str] = None,
        unique: bool = False,
        background: bool = False,
        sparse: bool = False,
        partialFilterExpression: dict[str, Any] | None = None,
    ) -> None: ...

    def list_indexes(self) -> AsyncIterator[dict[str, Any]]: ...

    async def find_one_and_update(
        self,
        filter: dict[str, Any],
        update: UpdateType,
        projection: Optional[dict[str, Any]] = None,
        # True for after, False for before
        return_document: bool = False,
        array_filters: list[dict[str, Any]] | None = None,
        upsert: bool = False,
    ) -> dict[str, Any] | None: ...

    async def find_one_and_delete(
        self,
        filter: dict[str, Any],
        projection: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]: ...

    async def distinct(self, key: str, filter: dict[str, Any], hint: str | None = None) -> list[Any]: ...

    async def bulk_write(self, operations: list[Any]) -> BulkWriteResult: ...


class AsyncDatabase(Protocol):
    """
    A type definition for the AsyncIOMotorDatabase class from the motor library.
    """

    def __getitem__(self, name: str) -> AsyncCollection: ...

    def get_collection(self, name: str, codec_options: Any) -> AsyncCollection: ...

    async def list_collection_names(self) -> list[str]: ...

    async def command(
        self,
        command: str | dict[str, Any],
        value: Any = 1,
        check: bool = True,
        allowable_errors: Sequence[str | int] | None = None,
        codec_options: None = None,
        session: ClientSession | None = None,
        comment: Any | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]: ...


class AsyncClient(Protocol):
    async def server_info(self) -> dict[str, Any]: ...

    def __getitem__(self, name: str) -> AsyncDatabase: ...


class RawAsyncCursor(Protocol):
    def __aiter__(self) -> "AsyncCursor": ...

    async def __anext__(self) -> dict[str, Any]: ...


class UpdateKwargs(TypedDict):
    filter: dict[str, Any]
    update: UpdateType
    upsert: NotRequired[bool]


class AsyncCursor(RawAsyncCursor):
    def limit(self, limit: int) -> "AsyncCursor": ...

    def skip(self, skip: int) -> "AsyncCursor": ...

    def sort(self, *sort: list[tuple[str, int]] | str | int) -> "AsyncCursor": ...

    def batch_size(self, batch_size: int) -> "RawAsyncCursor": ...

    def hint(self, index: str | list[tuple[str, Any]]) -> "AsyncCursor": ...

    def max_time_ms(self, max_time_ms: int | None) -> "AsyncCursor": ...
