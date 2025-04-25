from typing import Any

from pydantic import Field

from core.domain.tool import CustomTool
from core.storage.mongo.models.base_document import BaseDocumentWithID
from core.storage.mongo.models.pyobjectid import PyObjectID


class CustomToolDocument(BaseDocumentWithID):
    name: str = Field(description="The name of the tool")
    description: str = Field(default="", description="The description of the tool")
    parameters: dict[str, Any] = Field(description="The input parameters of the tool")

    @classmethod
    def from_domain(cls, tenant: str, tool: CustomTool) -> "CustomToolDocument":
        return cls(
            _id=PyObjectID.from_str(tool.id) if tool.id else None,
            tenant=tenant,
            name=tool.name,
            description=tool.description,
            parameters=tool.parameters,
        )

    def to_domain(self) -> CustomTool:
        return CustomTool(
            id=str(self.id) if self.id is not None else None,
            name=self.name,
            description=self.description,
            parameters=self.parameters,
        )
