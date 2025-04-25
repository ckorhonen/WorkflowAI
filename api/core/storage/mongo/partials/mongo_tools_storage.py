from typing import Any, Tuple

from bson import ObjectId

from core.domain.tool import CustomTool
from core.storage import ObjectNotFoundException
from core.storage.mongo.models.custom_tool_document import CustomToolDocument
from core.storage.mongo.mongo_types import AsyncCollection
from core.storage.mongo.utils import dump_model
from core.storage.tools_storage import ToolsStorage


class MongoToolsStorage(ToolsStorage):
    def __init__(self, tenant_tuple: Tuple[str, int], collection: AsyncCollection):
        self._tenant, _ = tenant_tuple
        self._collection = collection

    def _tenant_filter(self) -> dict[str, Any]:
        return {"tenant": self._tenant}

    async def list_tools(self) -> list[CustomTool]:
        cursor = self._collection.find(self._tenant_filter())
        tools: list[CustomTool] = []
        async for doc in cursor:
            tool_doc = CustomToolDocument.model_validate(doc)
            tools.append(tool_doc.to_domain())
        return tools

    async def get_tool_by_id(self, id: str) -> CustomTool:
        doc = await self._collection.find_one({**self._tenant_filter(), "_id": ObjectId(id)})
        if not doc:
            raise ObjectNotFoundException(f"Tool with ID '{id}' not found")
        tool_doc = CustomToolDocument.model_validate(doc)
        return tool_doc.to_domain()

    async def create_tool(self, name: str, description: str, input_schema: dict[str, Any]) -> CustomTool:
        existing = await self._collection.find_one({**self._tenant_filter(), "name": name})
        if existing:
            raise ValueError(f"Tool with name '{name}' already exists")
        tool_doc = CustomToolDocument.from_domain(
            tenant=self._tenant,
            tool=CustomTool(
                name=name,
                description=description,
                parameters=input_schema,
            ),
        )
        inserted = await self._collection.insert_one(dump_model(tool_doc))
        return CustomTool(
            id=str(inserted.inserted_id),
            name=name,
            description=description,
            parameters=input_schema,
        )

    async def update_tool(self, id: str, name: str, description: str, input_schema: dict[str, Any]) -> CustomTool:
        result = await self._collection.update_one(
            {**self._tenant_filter(), "_id": ObjectId(id)},
            {
                "$set": {
                    "name": name,
                    "description": description,
                    "parameters": input_schema,
                },
            },
        )
        if result.matched_count == 0:
            raise ObjectNotFoundException(f"Tool with ID '{id}' not found")
        return CustomTool(
            id=str(id),
            name=name,
            description=description,
            parameters=input_schema,
        )

    async def delete_tool(self, id: str) -> None:
        result = await self._collection.delete_one({**self._tenant_filter(), "_id": ObjectId(id)})
        if result.deleted_count == 0:
            raise ObjectNotFoundException(f"Tool with ID '{id}' not found")
