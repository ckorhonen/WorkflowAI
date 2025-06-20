from collections.abc import Iterator
from datetime import datetime, timedelta
from typing import Any

from api.routers.mcp._mcp_models import (
    AgentResponse,
    AgentSortField,
    AIEngineerReponseWithUsefulLinks,
    ConciseLatestModelResponse,
    ConciseModelResponse,
    LegacyMCPToolReturn,
    MajorVersion,
    MCPRun,
    MCPToolReturn,
    ModelSortField,
    PaginatedMCPToolReturn,
    SortOrder,
    UsefulLinks,
)
from api.routers.mcp._utils.agent_sorting import sort_agents
from api.routers.mcp._utils.model_sorting import sort_models
from api.services import tasks
from api.services.internal_tasks.ai_engineer_service import AIEngineerChatMessage, AIEngineerReponse, AIEngineerService
from api.services.models import ModelsService
from api.services.runs.runs_service import RunsService
from api.services.runs_search import RunsSearchService
from api.services.task_deployments import TaskDeploymentsService
from api.services.versions import VersionsService
from core.domain.agent_run import AgentRun
from core.domain.consts import WORKFLOWAI_APP_URL
from core.domain.models.model_data import FinalModelData, LatestModel
from core.domain.models.model_datas_mapping import MODEL_DATAS
from core.domain.models.models import Model
from core.domain.search_query import FieldQuery, SearchOperator
from core.domain.task_group import TaskGroup, TaskGroupQuery
from core.domain.task_info import TaskInfo
from core.domain.users import UserIdentifier
from core.domain.version_environment import VersionEnvironment
from core.storage import ObjectNotFoundException
from core.storage.backend_storage import BackendStorage
from core.storage.task_run_storage import TaskRunStorage
from core.utils.schemas import FieldType

# Claude Code only support 25k tokens, for example.
# Overall it's a good practice to limit the tool return tokens to avoid overflowing the coding agents context.
MAX_TOOL_RETURN_TOKENS = 20000


class MCPService:
    def __init__(
        self,
        storage: BackendStorage,
        ai_engineer_service: AIEngineerService,
        runs_service: RunsService,
        versions_service: VersionsService,
        models_service: ModelsService,
        task_deployments_service: TaskDeploymentsService,
        user_email: str | None,
        tenant_slug: str | None,
    ):
        self.storage = storage
        self.ai_engineer_service = ai_engineer_service
        self.runs_service = runs_service
        self.versions_service = versions_service
        self.models_service = models_service
        self.task_deployments_service = task_deployments_service
        self.user_email = user_email
        self.tenant_slug = tenant_slug

    def _get_useful_links(self, agent_id: str | None, agent_schema_id: int | None) -> UsefulLinks:
        if agent_id is None:
            agent_id = "<example_agent_id>"

        tenant_slug = self.tenant_slug

        return UsefulLinks(
            useful_links=[
                UsefulLinks.Link(
                    title="Agents list",
                    url=f"{WORKFLOWAI_APP_URL}/{tenant_slug}/agents",
                    description="View all agents in the user's organization, also allow to see the count of runs and cost of the last 7 days",
                ),
                UsefulLinks.Link(
                    title="API Keys management model",
                    url=f"{WORKFLOWAI_APP_URL}/keys",
                    description="View and create API keys for the user's organization",
                ),
                UsefulLinks.Link(
                    title="WorkflowAI playground",
                    url=f"{WORKFLOWAI_APP_URL}/{tenant_slug}/agents/{agent_id}/{agent_schema_id or 1}",
                    description="Main page of the WorkflowAI web app, allow to run agents on different models, update version messages, and more",
                ),
                UsefulLinks.Link(
                    title="Agent runs",
                    url=f"{WORKFLOWAI_APP_URL}/{tenant_slug}/agents/{agent_id}/{agent_schema_id or 1}/runs",
                    description="View runs for a specific agent",
                ),
                UsefulLinks.Link(
                    title="Agent versions",
                    url=f"{WORKFLOWAI_APP_URL}/{tenant_slug}/agents/{agent_id}/{agent_schema_id or 1}/versions",
                    description="View versions for a specific agent",
                ),
                UsefulLinks.Link(
                    title="Deployments",
                    url=f"{WORKFLOWAI_APP_URL}/{tenant_slug}/agents/{agent_id}/{agent_schema_id or 1}/deployments",
                    description="View deployments (deployed versions) for a specific agent",
                ),
                UsefulLinks.Link(
                    title="Agent side-by-side",
                    url=f"{WORKFLOWAI_APP_URL}/{tenant_slug}/agents/{agent_id}/{agent_schema_id or 1}/side-by-side",
                    description="View side-by-side comparison of two versions of an agent",
                ),
                UsefulLinks.Link(
                    title="Agent reviews",
                    url=f"{WORKFLOWAI_APP_URL}/{tenant_slug}/agents/{agent_id}/{agent_schema_id or 1}/reviews",
                    description="View reviews for a specific agent created by staff members in the organization",
                ),
                UsefulLinks.Link(
                    title="Agent benchmarks",
                    url=f"{WORKFLOWAI_APP_URL}/{tenant_slug}/agents/{agent_id}/{agent_schema_id or 1}/benchmarks",
                    description="View benchmarks for a specific agent, allow to compare different versions / models of an agent and compare their correctness, latency, and price",
                ),
                UsefulLinks.Link(
                    title="Agent feedback",
                    url=f"{WORKFLOWAI_APP_URL}/{tenant_slug}/agents/{agent_id}/{agent_schema_id or 1}/feedback",
                    description="View feedback for a specific agent created by end users (customers)",
                ),
                UsefulLinks.Link(
                    title="Agent cost",
                    url=f"{WORKFLOWAI_APP_URL}/{tenant_slug}/agents/{agent_id}/{agent_schema_id or 1}/cost",
                    description="View cost for a specific agent on different time frames (yesterday, last week, last month, last year, all time)",
                ),
                UsefulLinks.Link(
                    title="WorkflowAI offical documentation",
                    url="https://docs.workflowai.com",
                    description="Official documentation for WorkflowAI, including guides, API references, and more",
                ),
            ],
        )

    async def list_available_models(
        self,
        page: int,
        sort_by: ModelSortField,
        order: SortOrder,
        agent_id: str | None,
        agent_schema_id: int | None,
        agent_requires_tools: bool = False,
    ) -> PaginatedMCPToolReturn[None, ConciseModelResponse | ConciseLatestModelResponse]:
        if agent_id:
            if agent_schema_id is not None:
                agent = await self.storage.task_variant_latest_by_schema_id(agent_id, agent_schema_id)
            else:
                agent = await self.storage.task_variants.get_latest_task_variant(agent_id)

            if agent:
                models = await self.models_service.models_for_task(
                    agent,
                    instructions=None,
                    requires_tools=agent_requires_tools,
                )
                model_responses: list[ConciseModelResponse | ConciseLatestModelResponse] = [
                    ConciseModelResponse.from_model_for_task(m) for m in models if m.is_not_supported_reason is None
                ]
                sort_models(model_responses, sort_by, order)
                return PaginatedMCPToolReturn[None, ConciseModelResponse | ConciseLatestModelResponse](
                    success=True,
                    items=model_responses,
                ).paginate(max_tokens=MAX_TOOL_RETURN_TOKENS, page=page)

        def _model_data_iterator() -> Iterator[ConciseLatestModelResponse | ConciseModelResponse]:
            for model in Model:
                data = MODEL_DATAS[model]
                if isinstance(data, LatestModel):
                    points_to_model = MODEL_DATAS[data.model]
                    if isinstance(points_to_model, FinalModelData):
                        yield ConciseLatestModelResponse(
                            id=model.value,
                            currently_points_to=points_to_model.model.value,
                        )
                    continue
                elif isinstance(data, FinalModelData):
                    yield ConciseModelResponse.from_model_data(model.value, data)
                else:
                    # Skipping deprecated models
                    continue

        model_responses = list(_model_data_iterator())
        sort_models(model_responses, sort_by, order)

        return PaginatedMCPToolReturn[None, ConciseModelResponse | ConciseLatestModelResponse](
            success=True,
            items=model_responses,
        ).paginate(max_tokens=MAX_TOOL_RETURN_TOKENS, page=page)

    def _extract_agent_id_and_run_id(self, run_url: str) -> tuple[str, str]:  # noqa: C901
        """Extract the agent ID and run ID from the run URL.

        Supports multiple URL formats:
        1. https://workflowai.com/workflowai/agents/classify-email-domain/runs/019763ae-ba9f-70a9-8d44-5a626c82e888
        2. http://localhost:3000/workflowai/agents/sentiment/2/runs?taskRunId=019763a5-12a7-73b7-9b0c-e6413d2da52f

        Args:
            run_url: The run URL to parse

        Returns:
            A tuple of (agent_id, run_id)

        Raises:
            ValueError: If the URL format is invalid or doesn't match the expected pattern
        """
        if not run_url:
            raise ValueError("run_url must be a non-empty string")

        # Parse query parameters first
        from urllib.parse import parse_qs, urlparse

        parsed_url = urlparse(run_url)
        query_params = parse_qs(parsed_url.query)

        # Remove trailing slash from path
        clean_path = parsed_url.path.rstrip("/")

        # Split by "/" and filter out empty parts
        parts = [part for part in clean_path.split("/") if part]

        # Find "agents" keyword and extract agent_id
        try:
            agents_index = None
            for i, part in enumerate(parts):
                if part == "agents":
                    agents_index = i
                    break

            if agents_index is None or agents_index + 1 >= len(parts):
                raise ValueError(f"Could not find 'agents/{{agent_id}}' pattern in URL: {run_url}")

            agent_id = parts[agents_index + 1]
            if not agent_id:
                raise ValueError(f"Agent ID is empty in URL: {run_url}")

            # Look for run ID in different places
            run_id = None

            # Method 1: Check for taskRunId in query parameters
            if "taskRunId" in query_params and query_params["taskRunId"]:
                run_id = query_params["taskRunId"][0]

            # Method 2: Check for standard pattern agents/agent_id/runs/run_id
            if not run_id:
                # Look for "runs" after agent_id (may have schema_id in between)
                runs_index = None
                for i in range(agents_index + 2, len(parts)):
                    if parts[i] == "runs" and i + 1 < len(parts):
                        runs_index = i
                        break

                if runs_index is not None:
                    run_id = parts[runs_index + 1]

            # Method 3: Check for pattern agents/agent_id/schema_id/runs (runs list page with taskRunId param)
            if not run_id:
                # Look for pattern where "runs" comes after agent_id (with optional schema_id)
                for i in range(agents_index + 2, len(parts)):
                    if parts[i] == "runs":
                        # This is probably a runs list page, check query params again
                        if "taskRunId" in query_params and query_params["taskRunId"]:
                            run_id = query_params["taskRunId"][0]
                        break

            if not run_id:
                raise ValueError(f"Could not find run ID in URL: {run_url}")

            return agent_id, run_id

        except (IndexError, ValueError) as e:
            raise ValueError(f"Invalid run URL format: {run_url}") from e

    async def fetch_run_details(
        self,
        agent_id: str | None,
        run_id: str | None,
        run_url: str | None,
    ) -> MCPToolReturn[MCPRun]:
        """Fetch details of a specific agent run."""

        if run_url:
            try:
                agent_id, run_id = self._extract_agent_id_and_run_id(run_url)
                # find the task tuple from the agent id
            except ValueError:
                return MCPToolReturn(
                    success=False,
                    error="Invalid run URL, must be in the format 'https://workflowai.com/workflowai/agents/agent-id/runs/run-id', or you must pass 'agent_id' and 'run_id'",
                )

        if not agent_id:
            return MCPToolReturn(
                success=False,
                error="Agent ID is required",
            )

        if not run_id:
            return MCPToolReturn(
                success=False,
                error="Run ID is required",
            )

        task_info = await self.storage.tasks.get_task_info(agent_id)
        task_tuple = task_info.id_tuple
        if not task_tuple:
            return MCPToolReturn(
                success=False,
                error=f"Agent {agent_id} not found",
            )
        try:
            run = await self.runs_service.run_by_id(task_tuple, run_id)
        except ObjectNotFoundException:
            return MCPToolReturn(
                success=False,
                error=f"Run {run_id} not found",
            )

        # Retrieve variant to get output schema
        version = await self.storage.task_groups.get_task_group_by_id(task_tuple[0], run.group.id)
        # Version Properties should always have a variant id
        if variant_id := version.properties.task_variant_id:
            variant = await self.storage.task_version_resource_by_id(task_tuple[0], variant_id)
        else:
            variant = None

        mcp_run = MCPRun.from_domain(run, version, variant.output_schema.json_schema if variant else None)

        return MCPToolReturn(
            success=True,
            data=mcp_run,
        )

    async def list_agents(
        self,
        page: int,
        sort_by: AgentSortField,
        order: SortOrder,
        agent_id: str | None = None,
        stats_from_date: str = "",
        with_schemas: bool = False,
    ) -> PaginatedMCPToolReturn[None, AgentResponse]:
        """List all agents with their statistics."""
        try:
            # Parse from_date or use default
            parsed_from_date = None
            if stats_from_date:
                try:
                    parsed_from_date = datetime.fromisoformat(stats_from_date.replace("Z", "+00:00"))
                except ValueError:
                    pass

            if not parsed_from_date:
                parsed_from_date = datetime.now() - timedelta(days=7)

            # Get agent stats
            stats_by_uid: dict[int, TaskRunStorage.AgentRunCount] = {}
            async for stat in self.storage.task_runs.run_count_by_agent_uid(parsed_from_date):
                stats_by_uid[stat.agent_uid] = stat

            if agent_id:
                agents = [await tasks.get_task_by_id(self.storage, agent_id, with_schemas=with_schemas)]
            else:
                agents = await tasks.list_tasks(self.storage, with_schemas=with_schemas)

            # Enrich agents with stats
            agent_responses: list[AgentResponse] = []
            for agent in agents:
                # Get stats for this agent
                if agent.uid and agent.uid in stats_by_uid:
                    agent_stats: TaskRunStorage.AgentRunCount = stats_by_uid[agent.uid]
                    run_count: int = agent_stats.run_count
                    total_cost_usd: float = agent_stats.total_cost_usd
                else:
                    run_count: int = 0
                    total_cost_usd: float = 0.0

                # Build schemas from versions
                schemas = [
                    AgentResponse.AgentSchema(
                        agent_schema_id=v.schema_id,
                        created_at=v.created_at.isoformat() if v.created_at else None,
                        input_json_schema=v.input_schema,
                        output_json_schema=v.output_schema,
                        is_hidden=v.is_hidden or False,
                        last_active_at=v.last_active_at.isoformat() if v.last_active_at else None,
                    )
                    for v in agent.versions
                ]

                agent_response = AgentResponse(
                    agent_id=agent.id,
                    is_public=agent.is_public or False,
                    schemas=schemas,
                    run_count=run_count,
                    total_cost_usd=total_cost_usd,
                )

                agent_responses.append(agent_response)

            sort_agents(agent_responses, sort_by, order)

            return PaginatedMCPToolReturn[None, AgentResponse](
                success=True,
                items=agent_responses,
            ).paginate(max_tokens=MAX_TOOL_RETURN_TOKENS, page=page)

        except Exception as e:
            return PaginatedMCPToolReturn(
                success=False,
                error=f"Failed to list agents with stats: {str(e)}",
                data=None,
            )

    async def get_agent_version(
        self,
        task_tuple: tuple[str, int],
        version_id: str,
    ) -> PaginatedMCPToolReturn[
        None,
        MajorVersion,
    ]:  # We return a paginated response for typing simplicity to align with list_agent_versions
        try:
            # TODO: use a Pydantic model for the version
            version_data = await self.versions_service.get_version(task_tuple, version_id, self.models_service)

            # Convert to the same format as the existing endpoint
            major_version = MajorVersion.from_version(*version_data)

            return PaginatedMCPToolReturn[None, MajorVersion](
                success=True,
                items=[major_version],
            ).paginate(max_tokens=MAX_TOOL_RETURN_TOKENS, page=1)

        except ObjectNotFoundException:
            return PaginatedMCPToolReturn[None, MajorVersion](
                success=False,
                error=f"Version {version_id} not found for agent {task_tuple[0]}",
            )
        except Exception as e:
            return PaginatedMCPToolReturn[None, MajorVersion](
                success=False,
                error=f"Failed to get agent version: {str(e)}",
            )

    async def list_agent_versions(
        self,
        task_tuple: tuple[str, int],
        page: int,
        schema_id: int | None = None,
    ) -> PaginatedMCPToolReturn[None, MajorVersion]:
        """List all versions of a specific agent."""
        try:
            versions = await self.versions_service.list_version_majors(task_tuple, schema_id, self.models_service)
            major_versions = [MajorVersion.from_major(v) for v in versions]

            return PaginatedMCPToolReturn[None, MajorVersion](
                success=True,
                items=major_versions,
            ).paginate(max_tokens=MAX_TOOL_RETURN_TOKENS, page=page)

        except Exception as e:
            return PaginatedMCPToolReturn[None, MajorVersion](
                success=False,
                error=f"Failed to list agent versions: {str(e)}",
            )

    async def _get_agent_or_failed_tool_result(
        self,
        agent_id: str,
    ) -> tuple[TaskInfo | None, LegacyMCPToolReturn | None]:
        try:
            agent_info = await self.storage.tasks.get_task_info(agent_id)
        except ObjectNotFoundException:
            list_agent_tool_answer = await self.list_agents(page=1, sort_by="last_active_at", order="desc")

            return None, LegacyMCPToolReturn(
                success=False,
                error=f"Agent {agent_id} not found, please provide a valid agent id. Agent id can be found in either the model=... paramater (usually composed of '<agent_name>/<model_name>' or '<agent_name>/<agent_schema_id>/<deployment_environment>') or in the metadata of the agent run request. See 'data' for a list of existing agents for the user.",
                data={"user_agents": list_agent_tool_answer.items},
            )

        return agent_info, None

    async def ask_ai_engineer(
        self,
        agent_schema_id: int | None,
        agent_id: str | None,
        message: str,
        user_programming_language: str,
        user_code_extract: str,
    ) -> MCPToolReturn[AIEngineerReponseWithUsefulLinks] | LegacyMCPToolReturn:
        """Ask the AI Engineer a question (legacy endpoint)."""

        user_message = message

        agent_info: TaskInfo | None = None
        if agent_id:
            agent_info, error_tool_result = await self._get_agent_or_failed_tool_result(agent_id)
            if error_tool_result:
                return error_tool_result
            if agent_info:
                agent_schema_id = agent_schema_id or agent_info.latest_schema_id or 1

        # TODO: switch to a streamable MCP tool
        last_chunk: AIEngineerReponse | None = None
        async for chunk in self.ai_engineer_service.stream_ai_engineer_agent_response(
            task_tuple=agent_info.id_tuple if agent_info else None,
            agent_schema_id=agent_schema_id,
            user_email=self.user_email,
            messages=[AIEngineerChatMessage(role="USER", content=user_message)],
            user_programming_language=user_programming_language,
            user_code_extract=user_code_extract,
        ):
            last_chunk = chunk

        if last_chunk is None:
            return MCPToolReturn(
                success=False,
                error="No response from AI Engineer",
            )

        useful_links = self._get_useful_links(agent_id, agent_schema_id)
        return_value = AIEngineerReponseWithUsefulLinks.model_validate(
            {
                **last_chunk.model_dump(exclude_none=True),
                "useful_links": useful_links,
            },
        )

        return MCPToolReturn(
            success=True,
            data=return_value,
        )

    async def deploy_agent_version(
        self,
        task_tuple: tuple[str, int],
        version_id: str,
        environment: str,
        deployed_by: UserIdentifier,
    ) -> LegacyMCPToolReturn:
        """Deploy a specific version of an agent to an environment."""
        try:
            try:
                env = VersionEnvironment(environment.lower())
            except ValueError:
                return LegacyMCPToolReturn(
                    success=False,
                    error=f"Invalid environment '{environment}'. Must be one of: dev, staging, production",
                )

            deployment = await self.task_deployments_service.deploy_version(
                task_id=task_tuple,
                task_schema_id=None,
                version_id=version_id,
                environment=env,
                deployed_by=deployed_by,
            )

            # Build the model parameter for the migration guide
            model_param = f"{task_tuple[0]}/#{deployment.schema_id}/{environment}"

            # Create migration guide based on deployment documentation
            migration_guide: dict[str, Any] = {
                "model_parameter": model_param,
                "migration_instructions": {
                    "overview": "Update your code to point to the deployed version instead of hardcoded prompts",
                    "with_input_variables": {
                        "description": "If your prompt uses input variables (double curly braces)",
                        "before": {
                            "model": f"{task_tuple[0]}/your-model-name",
                            "messages": [{"role": "user", "content": "Your prompt with..."}],
                            "extra_body": {"input": {"variable": "value"}},
                        },
                        "after": {
                            "model": model_param,
                            "messages": [],  # Empty because prompt is stored in WorkflowAI
                            "extra_body": {"input": {"variable": "value"}},
                        },
                    },
                    "without_input_variables": {
                        "description": "If your prompt doesn't use input variables (e.g., chatbots with system messages)",
                        "before": {
                            "model": f"{task_tuple[0]}/your-model-name",
                            "messages": [
                                {"role": "system", "content": "Your system instructions"},
                                {"role": "user", "content": "user_message"},
                            ],
                        },
                        "after": {
                            "model": model_param,
                            "messages": [
                                {"role": "user", "content": "user_message"},
                            ],  # System message now comes from the deployment
                        },
                    },
                    "important_notes": [
                        "The messages parameter is always required, even if empty",
                        "Schema number defines the input/output contract",
                        f"This deployment uses schema #{deployment.schema_id}",
                        "Test thoroughly before deploying to production",
                    ],
                },
            }

            return LegacyMCPToolReturn(
                success=True,
                messages=[
                    f"Successfully deployed version {version_id} to {environment} environment",
                ],
                data={
                    "version_id": deployment.version_id,
                    "agent_schema_id": deployment.schema_id,
                    "environment": str(deployment.environment.value),
                    "deployed_at": deployment.deployed_at.isoformat() if deployment.deployed_at else "",
                    "migration_guide": migration_guide,
                },
            )

        except Exception as e:
            return LegacyMCPToolReturn(
                success=False,
                error=f"Failed to deploy version: {str(e)}",
            )

    async def _map_runs(self, task_tuple: tuple[str, int], runs: list[AgentRun]) -> list[MCPRun]:
        version_ids = {run.group.id for run in runs}

        variant_ids: set[str] = set()
        versions: dict[str, TaskGroup] = {}
        async for v in self.storage.task_groups.list_task_groups(
            TaskGroupQuery(
                task_id=task_tuple[0],
                ids=version_ids,
            ),
        ):
            versions[v.id] = v
            if v.properties.task_variant_id:
                variant_ids.add(v.properties.task_variant_id)

        schema_by_id: dict[int, dict[str, Any]] = {
            v.task_schema_id: v.output_schema.json_schema
            async for v in self.storage.task_variants.variants_iterator(task_tuple[0], variant_ids)
        }

        return [
            MCPRun.from_domain(run, versions.get(run.group.id), schema_by_id.get(run.task_schema_id)) for run in runs
        ]

    async def search_runs(  # noqa: C901
        self,
        task_tuple: tuple[str, int],
        # TODO: this should be a plain string
        # See https://linear.app/workflowai/issue/WOR-4976/write-doc-about-how-to-search-runs
        field_queries: list[dict[str, Any]],
        limit: int,
        offset: int,
        page: int,
        include_full_data: bool = True,
    ) -> PaginatedMCPToolReturn[None, MCPRun]:
        """Search agent runs by metadata fields."""
        try:
            # Convert the field queries to the proper format
            parsed_field_queries: list[FieldQuery] = []
            for query_dict in field_queries:
                try:
                    # Validate required fields
                    if "field_name" not in query_dict:
                        return PaginatedMCPToolReturn[None, MCPRun](
                            success=False,
                            error="Missing required field 'field_name' in field query",
                        )

                    if "operator" not in query_dict:
                        return PaginatedMCPToolReturn[None, MCPRun](
                            success=False,
                            error="Missing required field 'operator' in field query",
                        )

                    if "values" not in query_dict:
                        query_dict["values"] = []

                    # Parse the operator
                    try:
                        operator = SearchOperator(query_dict["operator"])
                    except ValueError:
                        return PaginatedMCPToolReturn[None, MCPRun](
                            success=False,
                            error=f"Invalid operator: {query_dict['operator']}. Valid operators are: {', '.join([op.value for op in SearchOperator])}",
                        )

                    # Parse the field type if provided
                    field_type: FieldType | None = None
                    if "type" in query_dict and query_dict["type"]:
                        field_type = query_dict["type"]

                    field_query = FieldQuery(
                        field_name=query_dict["field_name"],
                        operator=operator,
                        values=query_dict["values"],  # type: ignore
                        type=field_type,
                    )
                    parsed_field_queries.append(field_query)
                except Exception as e:
                    return PaginatedMCPToolReturn[None, MCPRun](
                        success=False,
                        error=f"Error parsing field query: {str(e)}",
                    )
            # Use the runs search service to perform the search
            search_service = RunsSearchService(self.storage)

            try:
                page_result = await search_service.search_task_runs(
                    task_uid=task_tuple,
                    field_queries=parsed_field_queries,
                    limit=limit,
                    offset=offset,
                    map=lambda x: x,
                    # tool_calls and llm_completions are not needed here
                    # tool_calls contains the entirety of tool calls executed during the request
                    # llm_completions contains each individual round trip with the LLM
                    # TODO: ultimately we should only need the "messages" field
                    exclude_fields={"llm_completions", "tool_calls"},
                )
            except Exception as e:
                return PaginatedMCPToolReturn[None, MCPRun](
                    success=False,
                    error=f"Failed to search runs: {str(e)}",
                )

            return PaginatedMCPToolReturn[None, MCPRun](
                success=True,
                items=await self._map_runs(task_tuple, page_result.items),
            ).paginate(max_tokens=MAX_TOOL_RETURN_TOKENS, page=page)

        except Exception as e:
            return PaginatedMCPToolReturn[None, MCPRun](
                success=False,
                error=f"Failed to search runs by metadata: {str(e)}",
            )
