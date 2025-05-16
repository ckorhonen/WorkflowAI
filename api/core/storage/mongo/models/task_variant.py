from datetime import datetime, timezone
from typing import Self

from pydantic import Field

from core.domain.fields.chat_message import ChatMessage
from core.domain.integration.integration_domain import IntegrationKind
from core.domain.task_variant import SerializableTaskVariant
from core.storage.mongo.models.pyobjectid import PyObjectID
from core.utils.fields import datetime_factory

from .base_document import BaseDocumentWithStrID
from .task_io import TaskIOSchema


class TaskVariantDocument(BaseDocumentWithStrID):
    created_at: datetime = Field(default_factory=datetime_factory)
    version: str = Field(..., description="The version of the task")
    slug: str = Field(..., description="An identifyer for a task. Stable accross schemas and versions")
    task_uid: int = Field(default=0, description="An index identifying the task, unique within a schema")
    schema_id: int = Field(..., description="An index identifying the schema, i-e the types of the input output")
    # TODO: remove, should be at task info level
    name: str
    input_schema: TaskIOSchema
    output_schema: TaskIOSchema
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # TODO: remove, should be at task info level
    is_public: bool | None = None
    creation_chat_messages: list[ChatMessage] | None = None
    used_integration_kind: IntegrationKind | None = None

    @classmethod
    def from_resource(cls, tenant: str, task: SerializableTaskVariant) -> Self:
        return cls(
            _id=PyObjectID.new(),
            version=task.id,
            task_uid=task.task_uid,
            tenant=tenant,
            slug=task.task_id.lower(),
            name=task.name,
            schema_id=task.task_schema_id,
            input_schema=TaskIOSchema.from_resource(task.input_schema),
            output_schema=TaskIOSchema.from_resource(task.output_schema),
            created_at=task.created_at,
            is_public=task.is_public,
            creation_chat_messages=task.creation_chat_messages,
            used_integration_kind=task.used_integration_kind,
        )

    def to_resource(self) -> SerializableTaskVariant:
        return SerializableTaskVariant(
            task_id=self.slug,
            task_uid=self.task_uid,
            task_schema_id=self.schema_id,
            id=self.version,
            name=self.name,
            input_schema=self.input_schema.to_resource(),
            output_schema=self.output_schema.to_resource(),
            created_at=self.created_at,
            is_public=self.is_public,
            creation_chat_messages=self.creation_chat_messages,
            tenant=self.tenant,
            used_integration_kind=self.used_integration_kind,
        )
