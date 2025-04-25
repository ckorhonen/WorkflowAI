import unittest
from unittest.mock import AsyncMock

from pymongo.errors import DuplicateKeyError

from core.domain.tool import CustomTool
from core.storage import ObjectNotFoundException
from core.storage.mongo.models.custom_tool_document import CustomToolDocument
from core.storage.mongo.partials.mongo_tools_storage import MongoToolsStorage


class TestMongoToolsStorage(unittest.TestCase):
    def setUp(self):
        self.collection = AsyncMock()
        self.tenant_tuple = ("test_tenant", 123)
        self.storage = MongoToolsStorage(self.tenant_tuple, self.collection)

    def test_tenant_filter(self):
        result = self.storage._tenant_filter()  # type: ignore[reportPrivateUsage]
        self.assertEqual(result, {"tenant": "test_tenant"})

    def test_tenant_uid_filter(self):
        result = self.storage._tenant_filter()  # type: ignore[reportPrivateUsage]
        self.assertEqual(result, {"tenant": "test_tenant"})

    async def test_list_tools(self):
        # Setup mock tool data
        tool1: CustomToolDocument = CustomToolDocument(
            name="tool1",
            description="Test tool 1",
            input_schema={},
        )
        tool2: CustomToolDocument = CustomToolDocument(
            name="tool2",
            description="Test tool 2",
            input_schema={},
        )

        # Mock the find method to return our test data
        self.collection.find.return_value.__aiter__.return_value = [tool1, tool2]

        # Call the method
        result = await self.storage.list_tools()

        # Verify results
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "tool1")
        self.assertEqual(result[1].name, "tool2")

        # Verify the find method was called with the right params
        self.collection.find.assert_called_once_with({"tenant": "test_tenant"})

    async def test_get_tool_found(self):
        # Setup mock tool data
        tool_data: CustomToolDocument = CustomToolDocument(
            name="test_tool",
            description="A test tool",
            input_schema={},
        )

        # Mock the find_one method to return our test data
        self.collection.find_one.return_value = tool_data

        # Call the method
        result = await self.storage.get_tool_by_id("test_tool")

        # Verify result
        self.assertEqual(result.name, "test_tool")
        self.assertEqual(result.description, "A test tool")

        # Verify the find_one method was called with the right params
        self.collection.find_one.assert_called_once_with({"name": "test_tool", "tenant": "test_tenant"})

    async def test_get_tool_not_found(self):
        # Mock the find_one method to return None (not found)
        self.collection.find_one.return_value = None

        # Call the method and expect an exception
        with self.assertRaises(ObjectNotFoundException):
            await self.storage.get_tool_by_id("nonexistent_tool")

        # Verify the find_one method was called with the right params
        self.collection.find_one.assert_called_once_with({"name": "nonexistent_tool", "tenant": "test_tenant"})

    async def test_create_tool_success(self):
        # Setup test tool
        tool: CustomTool = CustomTool(name="new_tool", description="A new tool", parameters={})

        # Mock the insert_one method
        self.collection.insert_one.return_value.inserted_id = "fake_id"

        # Call the method
        result = await self.storage.create_tool(
            tool.name,
            tool.description,
            tool.parameters,
        )

        # Verify result
        self.assertEqual(result.name, "new_tool")
        self.assertEqual(result.description, "A new tool")

        # Verify the insert_one method was called
        self.collection.insert_one.assert_called_once()
        # Check tenant and tenant_uid were added
        called_with = self.collection.insert_one.call_args[0][0]
        self.assertEqual(called_with["tenant"], "test_tenant")
        self.assertEqual(called_with["tenant_uid"], 123)

    async def test_create_tool_duplicate(self):
        # Setup test tool
        tool: CustomTool = CustomTool(name="existing_tool", description="An existing tool", parameters={})

        # Mock the insert_one method to raise DuplicateKeyError
        self.collection.insert_one.side_effect = DuplicateKeyError("Duplicate key error")

        # Call the method and expect an exception
        with self.assertRaises(ValueError):
            await self.storage.create_tool(tool.name, tool.description, tool.parameters)

    async def test_update_tool_success(self):
        # Setup test tool
        tool: CustomTool = CustomTool(name="updated_tool", description="Updated description", parameters={})

        # Mock the find_one_and_update method
        updated_doc: CustomToolDocument = CustomToolDocument(
            name="updated_tool",
            description="Updated description",
            input_schema={},
        )
        self.collection.find_one_and_update.return_value = updated_doc

        # Call the method
        result = await self.storage.update_tool(
            "existing_tool",
            tool.name,
            tool.description,
            tool.parameters,
        )

        # Verify result
        self.assertEqual(result.name, "updated_tool")
        self.assertEqual(result.description, "Updated description")

        # Verify the find_one_and_update method was called
        self.collection.find_one_and_update.assert_called_once()

    async def test_update_tool_not_found(self):
        # Setup test tool
        tool: CustomTool = CustomTool(name="updated_tool", description="Updated description", parameters={})

        # Mock the find_one_and_update method to return None (not found)
        self.collection.find_one_and_update.return_value = None

        # Call the method and expect an exception
        with self.assertRaises(ObjectNotFoundException):
            await self.storage.update_tool(
                "nonexistent_tool",
                tool.name,
                tool.description,
                tool.parameters,
            )

    async def test_delete_tool_success(self):
        # Mock the delete_one method to indicate successful deletion
        self.collection.delete_one.return_value.deleted_count = 1

        # Call the method
        await self.storage.delete_tool("existing_tool")

        # Verify the delete_one method was called
        self.collection.delete_one.assert_called_once_with({"name": "existing_tool", "tenant": "test_tenant"})

    async def test_delete_tool_not_found(self):
        # Mock the delete_one method to indicate no deletion
        self.collection.delete_one.return_value.deleted_count = 0

        # Call the method and expect an exception
        with self.assertRaises(ObjectNotFoundException):
            await self.storage.delete_tool("nonexistent_tool")

        # Verify the delete_one method was called
        self.collection.delete_one.assert_called_once_with({"name": "nonexistent_tool", "tenant": "test_tenant"})
