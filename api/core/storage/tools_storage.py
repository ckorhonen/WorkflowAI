from abc import ABC, abstractmethod
from typing import Any

from core.domain.tool import CustomTool


class ToolsStorage(ABC):
    @abstractmethod
    async def list_tools(self) -> list[CustomTool]:
        """List all tools for the current tenant."""
        pass

    @abstractmethod
    async def get_tool_by_id(self, id: str) -> CustomTool:
        """Get a specific tool by id."""
        pass

    @abstractmethod
    async def create_tool(self, name: str, description: str, input_schema: dict[str, Any]) -> CustomTool:
        """Create a new tool and return it with a generated UID."""
        pass

    @abstractmethod
    async def update_tool(self, id: str, name: str, description: str, input_schema: dict[str, Any]) -> CustomTool:
        """Update an existing tool by id."""
        pass

    @abstractmethod
    async def delete_tool(self, id: str) -> None:
        """Delete a tool by id."""
        pass
