from unittest.mock import AsyncMock, Mock, patch

import pytest

from api.services.internal_tasks.internal_tasks_service import (
    InternalTasksService,
)
from core.agents.url_finder_agent import URLFinderAgentInput
from core.tools import ToolKind


@pytest.fixture(scope="function")
def internal_tasks_service(mock_storage: Mock, mock_event_router: Mock):
    return InternalTasksService(storage=mock_storage, event_router=mock_event_router)


class TestSanitizeRequiredTools:
    async def test_web_browser_text_scraping_agent(
        self,
        internal_tasks_service: InternalTasksService,
    ):
        # Test case where WEB_BROWSER_TEXT is picked and agent is a scraping agent
        with patch(
            "api.services.internal_tasks.internal_tasks_service.url_finder_agent",
            new_callable=AsyncMock,
        ) as mock_url_finder:
            mock_url_finder.return_value.is_schema_containing_url = True

            result = await internal_tasks_service._sanitize_required_tools(  # pyright: ignore[reportPrivateUsage]
                task_name="test_task",
                input_json_schema={"type": "object"},
                required_tools_picking_run_id="test_run_id",
                picked_tools={ToolKind.WEB_BROWSER_TEXT},
            )

            assert result == {ToolKind.WEB_BROWSER_TEXT}
            mock_url_finder.assert_awaited_once_with(
                URLFinderAgentInput(
                    agent_name="test_task",
                    agent_input_json_schema={"type": "object"},
                ),
            )

    async def test_web_browser_text_not_scraping_agent(
        self,
        internal_tasks_service: InternalTasksService,
    ):
        # Test case where WEB_BROWSER_TEXT is picked but agent is not a scraping agent
        with patch(
            "api.services.internal_tasks.internal_tasks_service.url_finder_agent",
            new_callable=AsyncMock,
        ) as mock_url_finder:
            mock_url_finder.return_value.is_schema_containing_url = False

            result = await internal_tasks_service._sanitize_required_tools(  # pyright: ignore[reportPrivateUsage]
                task_name="test_task",
                input_json_schema={"type": "object"},
                required_tools_picking_run_id="test_run_id",
                picked_tools={ToolKind.WEB_BROWSER_TEXT},
            )

            assert result == set()
            mock_url_finder.assert_awaited_once_with(
                URLFinderAgentInput(
                    agent_name="test_task",
                    agent_input_json_schema={"type": "object"},
                ),
            )

    async def test_web_browser_text_url_finder_fails(
        self,
        internal_tasks_service: InternalTasksService,
    ):
        # Test case where WEB_BROWSER_TEXT is picked but URL finder agent fails
        with patch(
            "api.services.internal_tasks.internal_tasks_service.url_finder_agent",
            new_callable=AsyncMock,
            side_effect=Exception("Test error"),
        ) as mock_url_finder:
            result = await internal_tasks_service._sanitize_required_tools(  # pyright: ignore[reportPrivateUsage]
                task_name="test_task",
                input_json_schema={"type": "object"},
                required_tools_picking_run_id="test_run_id",
                picked_tools={ToolKind.WEB_BROWSER_TEXT},
            )

            assert result == set()
            mock_url_finder.assert_awaited_once_with(
                URLFinderAgentInput(
                    agent_name="test_task",
                    agent_input_json_schema={"type": "object"},
                ),
            )

    async def test_other_tools(
        self,
        internal_tasks_service: InternalTasksService,
    ):
        # Test case where other tools are picked
        result = await internal_tasks_service._sanitize_required_tools(  # pyright: ignore[reportPrivateUsage]
            task_name="test_task",
            input_json_schema={"type": "object"},
            required_tools_picking_run_id="test_run_id",
            picked_tools={ToolKind.WEB_SEARCH_GOOGLE},
        )

        assert result == {ToolKind.WEB_SEARCH_GOOGLE}

    async def test_multiple_tools_with_web_browser(
        self,
        internal_tasks_service: InternalTasksService,
    ):
        # Test case where WEB_BROWSER_TEXT is picked along with other tools
        result = await internal_tasks_service._sanitize_required_tools(  # pyright: ignore[reportPrivateUsage]
            task_name="test_task",
            input_json_schema={"type": "object"},
            required_tools_picking_run_id="test_run_id",
            picked_tools={ToolKind.WEB_BROWSER_TEXT, ToolKind.WEB_SEARCH_GOOGLE},
        )

        assert result == {ToolKind.WEB_BROWSER_TEXT, ToolKind.WEB_SEARCH_GOOGLE}
