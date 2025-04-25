from typing import Any

from pydantic import BaseModel, Field

from core.domain.tool import CustomTool


class ToolParamsRequest(BaseModel):
    name: str = Field(description="The name of the tool")
    description: str = Field(description="The description of the tool")
    input_schema: dict[str, Any] = Field(description="The input class of the tool")


class ToolResponse(BaseModel):
    id: str
    name: str = Field(description="The name of the tool")
    description: str = Field(description="The description of the tool")
    parameters: dict[str, Any] = Field(description="The input parameters of the tool")

    @classmethod
    def from_domain(cls, tool: CustomTool) -> "ToolResponse":
        if not tool.id:
            raise ValueError("tool.id is required to return a ToolResponse")

        return cls(
            id=tool.id,
            name=tool.name,
            description=tool.description,
            parameters=tool.parameters,
        )

    def to_domain(self) -> CustomTool:
        return CustomTool(
            id=str(self.id) if self.id else None,
            name=self.name,
            description=self.description,
            parameters=self.parameters,
        )
