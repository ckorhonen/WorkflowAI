from datetime import datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from api.dependencies.services import MetaAgentServiceDep, ModelsServiceDep, VersionsServiceDep
from api.dependencies.storage import StorageDep
from api.dependencies.task_info import TaskTupleDep
from api.schemas.user_identifier import UserIdentifier
from api.schemas.version_properties import ShortVersionProperties
from api.services.documentation_service import DocumentationService
from api.services.internal_tasks.meta_agent_service import MetaAgentChatMessage, PlaygroundState
from api.tags import RouteTags
from core.domain.fields.chat_message import ChatMessage
from core.domain.message import Message
from core.domain.models.models import Model
from core.domain.task_group import TaskGroup
from core.domain.task_group_properties import TaskGroupProperties
from core.domain.task_variant import SerializableTaskVariant
from core.domain.version_environment import VersionEnvironment
from core.domain.version_major import VersionDeploymentMetadata, VersionMajor
from core.utils.fields import datetime_zero

router = APIRouter(prefix="/_mcp", tags=[RouteTags.MCP], include_in_schema=False)
"""A specific router for MCP. This way we can maintain routes separately."""


class _VersionDeploymentMetadata(BaseModel):
    environment: VersionEnvironment
    deployed_at: datetime
    deployed_by: UserIdentifier | None

    @classmethod
    def from_domain(cls, deployment: VersionDeploymentMetadata):
        return cls(
            environment=deployment.environment,
            deployed_at=deployment.deployed_at,
            deployed_by=UserIdentifier.from_domain(deployment.deployed_by),
        )


class _MajorVersionProperties(BaseModel):
    temperature: float
    instructions: str | None
    messages: list[Message] | None
    task_variant_id: str | None

    @classmethod
    def from_domain(cls, properties: VersionMajor.Properties | TaskGroupProperties):
        return cls(
            temperature=properties.temperature or 0.0,
            instructions=properties.instructions,
            messages=properties.messages,
            task_variant_id=properties.task_variant_id,
        )


class _MinorVersion(BaseModel):
    minor: int
    id: str
    model: Model | str

    deployments: list[_VersionDeploymentMetadata] | None

    cost_estimate_usd: float | None

    last_active_at: datetime | None

    is_favorite: bool | None

    favorited_by: UserIdentifier | None

    created_by: UserIdentifier | None

    notes: str | None

    run_count: int | None

    properties: ShortVersionProperties

    @classmethod
    def from_minor(cls, minor: VersionMajor.Minor):
        return cls(
            id=minor.id,
            minor=minor.minor,
            properties=ShortVersionProperties(
                model=minor.properties.model,
                provider=minor.properties.provider,
                temperature=minor.properties.temperature,
            ),
            model=minor.properties.model,
            deployments=[_VersionDeploymentMetadata.from_domain(d) for d in minor.deployments]
            if minor.deployments
            else None,
            cost_estimate_usd=minor.cost_estimate_usd,
            last_active_at=minor.last_active_at,
            is_favorite=minor.is_favorite,
            notes=minor.notes,
            run_count=minor.run_count,
            favorited_by=UserIdentifier.from_domain(minor.favorited_by),
            created_by=UserIdentifier.from_domain(minor.created_by),
        )

    @classmethod
    def from_version(
        cls,
        version: TaskGroup,
        deployments: list[VersionDeploymentMetadata] | None,
        cost_estimate_usd: float | None,
        variant: SerializableTaskVariant | None,
    ):
        return cls(
            id=version.id,
            minor=version.semver.minor if version.semver else 0,
            model=version.properties.model or "",
            deployments=[_VersionDeploymentMetadata.from_domain(d) for d in deployments] if deployments else None,
            cost_estimate_usd=cost_estimate_usd,
            last_active_at=version.last_active_at,
            is_favorite=version.is_favorite,
            notes=version.notes,
            run_count=version.run_count,
            favorited_by=UserIdentifier.from_domain(version.favorited_by),
            created_by=UserIdentifier.from_domain(version.created_by),
            properties=ShortVersionProperties(
                model=version.properties.model,
                provider=version.properties.provider,
                temperature=version.properties.temperature,
            ),
        )


# TODO: clarify what data is needed here
class MajorVersion(BaseModel):
    major: int
    schema_id: int

    minors: list[_MinorVersion]

    created_by: UserIdentifier | None

    created_at: datetime

    properties: _MajorVersionProperties

    @classmethod
    def from_major(cls, version: VersionMajor):
        return cls(
            major=version.major,
            schema_id=version.schema_id,
            created_by=UserIdentifier.from_domain(version.created_by),
            created_at=version.created_at,
            minors=[_MinorVersion.from_minor(m) for m in version.minors],
            properties=_MajorVersionProperties.from_domain(version.properties),
        )

    @classmethod
    def from_version(
        cls,
        version: TaskGroup,
        deployments: list[VersionDeploymentMetadata] | None,
        cost_estimate_usd: float | None,
        variant: SerializableTaskVariant | None,
    ):
        return cls(
            major=version.semver.major if version.semver else 0,
            schema_id=version.schema_id,
            created_by=UserIdentifier.from_domain(version.created_by),
            created_at=version.created_at or datetime_zero(),
            minors=[_MinorVersion.from_version(version, deployments, cost_estimate_usd, variant)],
            properties=_MajorVersionProperties.from_domain(version.properties),
        )


@router.get(
    "/agents/{task_id}/versions",
    operation_id="get_agent_versions",
    description="""
<when_to_use>
When the user wants to retrieve details of versions of a WorkflowAI agent, or when they want to compare a specific version of an agent.
</when_to_use>
<returns>
Returns the details of one or more versions of a WorkflowAI agent.
</returns>
""",
)
async def get_agent_versions(
    versions_service: VersionsServiceDep,
    models_service: ModelsServiceDep,
    task_tuple: TaskTupleDep,
    version_id: str | None = Query(
        description="An optional version id, e-g 1.1. If not provided all versions are returned",
        default=None,
    ),
) -> list[MajorVersion]:
    if version_id:
        v = await versions_service.get_version(task_tuple, version_id, models_service)
        return [MajorVersion.from_version(*v)]
    versions = await versions_service.list_version_majors(task_tuple, None, models_service)
    return [MajorVersion.from_major(v) for v in versions]


class AskAIEngineerRequest(BaseModel):
    agent_schema_id: int | None = Field(
        description="The schema ID of the user's agent version, if known",
        default=None,
    )
    agent_id: str | None = Field(
        description="The id of the user's agent, example: 'email-filtering-agent'. Pass 'new' when the user wants to create a new agent.",
        default=None,
    )
    message: str = Field(
        description="Your message to the AI engineer about what help you need",
        default="I need help improving my agent",
    )


class AskAIEngineerResponse(BaseModel):
    response: str


@router.post("/ask-ai-engineer", operation_id="ask_ai_engineer", description="Ask the AI Engineer a question")
async def ask_ai_engineer(
    request: AskAIEngineerRequest,
    meta_agent_service: MetaAgentServiceDep,
    storage: StorageDep,
) -> AskAIEngineerResponse:
    if not request.agent_id or request.agent_id == "new":
        # Find the relevant section in the documentation
        relevant_docs = await DocumentationService().get_relevant_doc_sections(
            chat_messages=[ChatMessage(role="USER", content=request.message)],
            agent_instructions="",
        )
        return AskAIEngineerResponse(
            response=f"""Here are some relevant documentation from WorkflowAI for your request:
                {"\n".join([f"- {doc.title}: {doc.content}" for doc in relevant_docs])}
                """,
        )

    task_info = await storage.tasks.get_task_info(request.agent_id)
    # TODO: figure out the right schema id to use here
    schema_id = request.agent_schema_id or task_info.latest_schema_id or 1

    last_messages: list[MetaAgentChatMessage] = []
    async for messages in meta_agent_service.stream_proxy_meta_agent_response(
        task_tuple=task_info.id_tuple,
        agent_schema_id=schema_id,
        user_email=None,  # TODO:
        messages=[MetaAgentChatMessage(role="USER", content=request.message)],
        playground_state=PlaygroundState(
            is_proxy=True,
            selected_models=PlaygroundState.SelectedModels(column_1=None, column_2=None, column_3=None),
            agent_run_ids=[],
        ),
    ):
        last_messages = messages

    return AskAIEngineerResponse(response="\n\n".join([message.content for message in last_messages]))
