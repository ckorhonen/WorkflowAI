# pyright: reportPrivateUsage=false

from unittest.mock import Mock

import pytest

from api.routers.openai_proxy._openai_proxy_handler import OpenAIProxyHandler
from api.routers.openai_proxy._openai_proxy_models import (
    OpenAIProxyChatCompletionRequest,
    OpenAIProxyMessage,
    OpenAIProxyTool,
    OpenAIProxyToolFunction,
)
from core.domain.task_group_properties import TaskGroupProperties
from core.domain.tenant_data import PublicOrganizationData
from core.domain.tool import Tool
from tests import models as test_models


@pytest.fixture
def proxy_handler(
    mock_group_service: Mock,
    mock_storage: Mock,
    mock_run_service: Mock,
    mock_event_router: Mock,
):
    return OpenAIProxyHandler(
        group_service=mock_group_service,
        storage=mock_storage,
        run_service=mock_run_service,
        event_router=mock_event_router,
    )


class TestPrepareRun:
    @pytest.fixture
    def completion_request(self):
        return OpenAIProxyChatCompletionRequest(
            model="gpt-4o",
            messages=[
                OpenAIProxyMessage(role="user", content="Hello, world!"),
            ],
        )

    async def test_deployment_tools_overriden(
        self,
        proxy_handler: OpenAIProxyHandler,
        completion_request: OpenAIProxyChatCompletionRequest,
        mock_storage: Mock,
    ):
        """Check that the tools are overriden when provided in the completion request"""

        completion_request.model = "my-agent/#1/production"
        completion_request.tools = [
            OpenAIProxyTool(
                type="function",
                function=OpenAIProxyToolFunction(
                    name="my_function",
                    parameters={},
                    strict=True,
                ),
            ),
        ]
        mock_storage.task_deployments.get_task_deployment.return_value = test_models.task_deployment(
            properties=TaskGroupProperties(
                model="gpt-4o",
                task_variant_id="my-variant",  # type: ignore
                enabled_tools=["hello"],
            ),
        )
        mock_storage.task_version_resource_by_id.return_value = test_models.task_variant(
            input_schema={},
            output_schema={},
        )
        result = await proxy_handler._prepare_run(completion_request, PublicOrganizationData())
        assert result.properties.enabled_tools == [
            Tool(name="my_function", input_schema={}, output_schema={}, strict=True),
        ]
