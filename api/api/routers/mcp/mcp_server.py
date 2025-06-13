from typing import Annotated

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_request
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException

from api.routers.mcp._mcp_models import MCPToolReturn
from api.routers.mcp._mcp_service import MCPService
from api.services import file_storage, storage
from api.services.analytics import analytics_service
from api.services.event_handler import system_event_router, tenant_event_router
from api.services.feedback_svc import FeedbackService
from api.services.internal_tasks.internal_tasks_service import InternalTasksService
from api.services.internal_tasks.meta_agent_service import MetaAgentService
from api.services.models import ModelsService
from api.services.providers_service import shared_provider_factory
from api.services.reviews import ReviewsService
from api.services.runs.runs_service import RunsService
from api.services.security_service import SecurityService
from api.services.versions import VersionsService
from core.domain.analytics_events.analytics_events import OrganizationProperties, UserProperties

_mcp = FastMCP("WorkflowAI 🚀", stateless_http=True)  # pyright: ignore [reportUnknownVariableType]


async def get_mcp_service():
    request = get_http_request()

    _system_storage = storage.system_storage(storage.shared_encryption())
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    security_service = SecurityService(
        _system_storage.organizations,
        system_event_router(),
        analytics_service(user_properties=None, organization_properties=None, task_properties=None),
    )
    tenant = await security_service.find_tenant(None, auth_header.split(" ")[1])
    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid bearer token")
    org_properties = OrganizationProperties.build(tenant)
    # TODO: user analytics
    user_properties: UserProperties | None = None
    event_router = tenant_event_router(tenant.tenant, tenant.uid, user_properties, org_properties, None)
    _storage = storage.storage_for_tenant(tenant.tenant, tenant.uid, event_router, storage.shared_encryption())
    analytics = analytics_service(
        user_properties=user_properties,
        organization_properties=org_properties,
        task_properties=None,
    )
    models_service = ModelsService(storage=_storage)
    runs_service = RunsService(
        storage=_storage,
        provider_factory=shared_provider_factory(),
        event_router=event_router,
        analytics_service=analytics,
        file_storage=file_storage.shared_file_storage,
    )
    feedback_service = FeedbackService(storage=_storage.feedback)
    versions_service = VersionsService(storage=_storage, event_router=event_router)
    internal_tasks = InternalTasksService(event_router=event_router, storage=_storage)
    reviews_service = ReviewsService(
        backend_storage=_storage,
        internal_tasks=internal_tasks,
        event_router=event_router,
    )
    meta_agent_service = MetaAgentService(
        storage=_storage,
        event_router=event_router,
        runs_service=runs_service,
        models_service=models_service,
        feedback_service=feedback_service,
        versions_service=versions_service,
        reviews_service=reviews_service,
    )

    return MCPService(
        storage=_storage,
        meta_agent_service=meta_agent_service,
        runs_service=runs_service,
        versions_service=versions_service,
        models_service=models_service,
    )


@_mcp.tool()
async def list_available_models() -> MCPToolReturn:
    """<when_to_use>
    When you need to pick a model for the user's WorkflowAI agent, or any model-related goal.
    </when_to_use>
    <returns>
    Returns a list of all available AI models from WorkflowAI.
    </returns>"""
    service = await get_mcp_service()
    return await service.list_available_models()


@_mcp.tool()
async def list_agents_with_stats(
    from_date: Annotated[
        str,
        "ISO date string to filter stats from (e.g., '2024-01-01T00:00:00Z'). Defaults to 7 days ago if not provided.",
    ],
) -> MCPToolReturn:
    """<when_to_use>
    When the user wants to see all agents they have created, along with their statistics (run counts and costs on the last 7 days).
    </when_to_use>
    <returns>
    Returns a list of all agents for the user along with their statistics (run counts and costs).
    </returns>"""
    service = await get_mcp_service()
    return await service.list_agents_with_stats(from_date)


class AskAIEngineerRequest(BaseModel):
    agent_schema_id: int | None = Field(
        description="The schema ID of the user's agent version, if known from model=<agent_id>/<agent_schema_id>/<deployment_environment> when the workflowAI agent is already deployed",
        default=None,
    )
    agent_id: str | None = Field(
        description="The id of the user's agent, example: 'email-filtering-agent' in 'model=email-filtering-agent/gpt-4o-latest'. Pass 'new' when the user wants to create a new agent.",
        default=None,
    )
    message: str = Field(
        description="Your message to the AI engineer about what help you need",
        default="I need help improving my agent",
    )
    user_programming_language: str = Field(
        description="The programming language and integration (if known) used by the user, e.g, Typescript, Python with OpenAI SDK, etc.",
        default="python",
    )
    user_code_extract: str | None = Field(
        description="The code you are working on to improve the user's agent, if any. Please DO NOT include API keys or other sensitive information.",
        default=None,
    )


@_mcp.tool()
async def ask_ai_engineer(request: AskAIEngineerRequest) -> MCPToolReturn:
    """
    <when_to_use>
    Most user request about WorkflowAI must be processed by starting a conversation with the AI engineer agent to get insight about the WorkflowAI platform and the user's agents.
    </when_to_use>

    <returns>
    Returns a response from WorkflowAI's AI engineer (meta agent) to help improve your agent.
    </returns>
    Get a response from WorkflowAI's AI engineer (meta agent) to help improve your agent.
    """
    service = await get_mcp_service()
    return await service.ask_ai_engineer(
        agent_schema_id=request.agent_schema_id,
        agent_id=request.agent_id,
        message=request.message,
        user_programming_language=request.user_programming_language,
        user_code_extract=request.user_code_extract,
    )


def mcp_http_app():
    return _mcp.http_app(path="/sse")
