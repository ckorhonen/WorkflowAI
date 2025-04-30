from typing import Any, Optional, Self

from bson import ObjectId

from core.domain.task_example import SerializableTaskExample
from core.domain.task_example_query import SerializableTaskExampleQuery
from core.domain.task_variant import SerializableTaskVariant
from core.storage.mongo.utils import projection, query_set_filter

from .base_document import BaseDocumentWithID
from .pyobjectid import PyObjectID
from .task_metadata import TaskMetadataSchema
from .task_query import build_task_query_filter


class TaskExampleDocument(BaseDocumentWithID):
    """Schema for a task example"""

    task: TaskMetadataSchema | None = None

    task_input_hash: str = ""
    task_input: Any = {}
    task_input_preview: str = ""

    task_output_hash: str = ""
    task_output: Any = {}
    task_output_preview: str = ""

    from_task_run_id: str | None = None

    # Field is false by default
    in_training_set: bool = False

    task_input_vector: Optional[list[float]] = None

    # Field could be none when we do not have the data
    from_correction: Optional[bool] = None

    @classmethod
    def build_filter(cls, tenant: str, query: SerializableTaskExampleQuery) -> dict[str, Any]:
        filter = build_task_query_filter(tenant, query)

        if query.is_training is not None:
            filter["in_training_set"] = query.is_training

        if query.from_correction is not None:
            filter["from_correction"] = query.from_correction

        if query.ids:
            filter["_id"] = query_set_filter(query.ids, True)

        if query.task_input_hashes:
            filter["task_input_hash"] = query_set_filter(query.task_input_hashes, True)

        if query.task_input_vector:
            if not query.limit:
                raise AssertionError("limit is required when using a vector search")
            # Switching to atlas search syntax
            filter = {
                "$vectorSearch": {
                    # MDB documentation talks "indexed fields"
                    # so it might not work if a field is not indexed +
                    # filter operators are limited.
                    "filter": filter,
                    "index": "task_example_task_input_vector",
                    "path": "task_input_vector",
                    "queryVector": query.task_input_vector,
                    "limit": query.limit,
                    # MongoDB Atlas recommends to use 10 to 20
                    # times the number of desired documents to have a good compromise
                    # Between latency and accuracy
                    "numCandidates": query.limit * 10,
                },
            }

        return filter

    @classmethod
    def sort_by(cls, by: SerializableTaskExampleQuery.SortBy) -> tuple[str, int]:
        if by == SerializableTaskExampleQuery.SortBy.CREATED_AT:
            return "_id", 1
        if by == SerializableTaskExampleQuery.SortBy.RECENT:
            return "_id", -1
        raise AssertionError(f"Invalid sort by: {by}")

    @classmethod
    def from_resource(cls, tenant: str, task: SerializableTaskVariant, res: SerializableTaskExample) -> Self:
        return cls(
            _id=PyObjectID.from_str(res.id),
            tenant=tenant,
            task=TaskMetadataSchema.from_resource(task),
            task_input=res.task_input,
            task_input_hash=res.task_input_hash,
            task_input_preview=res.task_input_preview,
            task_output=res.task_output,
            task_output_hash=res.task_output_hash,
            task_output_preview=res.task_output_preview,
            from_task_run_id=res.from_task_run_id,
            task_input_vector=res.task_input_vector,
            from_correction=res.from_correction,
        )

    def to_resource(self) -> SerializableTaskExample:
        return SerializableTaskExample(
            id=str(self.id) if self.id else "",
            task_id=self.task.id if self.task else "",
            task_schema_id=self.task.schema_id if self.task else 0,
            task_input=self.task_input,
            task_input_hash=self.task_input_hash,
            task_input_preview=self.task_input_preview,
            task_output=self.task_output,
            task_output_hash=self.task_output_hash,
            task_output_preview=self.task_output_preview,
            from_task_run_id=self.from_task_run_id,
            task_input_vector=self.task_input_vector,
            from_correction=self.from_correction,
            created_at=ObjectId(self.id).generation_time if ObjectId.is_valid(self.id) else None,
        )

    @classmethod
    def build_project(cls, query: SerializableTaskExampleQuery) -> Optional[dict[str, Any]]:
        return projection(include=query.include_fields, exclude=query.exclude_fields)
