import json
import logging
from typing import Any

from fastapi import APIRouter, Request, Response

from api.dependencies.event_router import EventRouterDep
from api.dependencies.security import RequiredUserOrganizationDep
from api.dependencies.services import GroupServiceDep, RunServiceDep
from api.dependencies.storage import StorageDep
from api.routers.openai_proxy_models import (
    EnvironmentRef,
    OpenAIProxyChatCompletionChunk,
    OpenAIProxyChatCompletionRequest,
    OpenAIProxyChatCompletionResponse,
    OpenAIProxyResponseFormat,
)
from api.services.openai_proxy_service import OpenAIProxyService
from api.utils import get_start_time
from core.domain.consts import INPUT_KEY_MESSAGES
from core.domain.errors import BadRequestError
from core.domain.events import ProxyAgentCreatedEvent
from core.domain.message import Messages
from core.domain.task_group_properties import TaskGroupProperties
from core.domain.task_io import RawJSONMessageSchema, RawMessagesSchema, RawStringMessageSchema, SerializableTaskIO
from core.domain.task_variant import SerializableTaskVariant
from core.domain.types import AgentOutput
from core.domain.version_reference import VersionReference
from core.providers.base.provider_error import MissingModelError
from core.storage import ObjectNotFoundException
from core.utils.schemas import schema_from_data
from core.utils.strings import to_pascal_case
from core.utils.templates import extract_variable_schema

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["openai"])


def _raw_string_mapper(output: Any) -> str:
    return output


def _output_json_mapper(output: AgentOutput) -> str:
    return json.dumps(output)


def _json_schema_from_input(messages: Messages, input: dict[str, Any] | None) -> SerializableTaskIO:
    templatable = " ".join(messages.content_iterator())
    schema_from_input: dict[str, Any] | None = schema_from_data(input) if input else None
    schema_from_template = extract_variable_schema(templatable, existing_schema=schema_from_input)
    if not schema_from_template:
        if schema_from_input:
            raise BadRequestError("Input variables are provided but the messages do not contain a valid template")
        return RawMessagesSchema
    if not schema_from_input:
        raise BadRequestError("Messages are templated but no input variables are provided")
    return SerializableTaskIO.from_json_schema({**schema_from_template, "format": "messages"}, streamline=True)


def _build_variant(
    messages: Messages,
    agent_slug: str | None,
    input: dict[str, Any] | None,
    response_format: OpenAIProxyResponseFormat | None,
):
    input_schema = _json_schema_from_input(messages, input)

    if response_format:
        match response_format.type:
            case "text":
                output_schema = RawStringMessageSchema
            case "json_object":
                output_schema = RawJSONMessageSchema
            case "json_schema":
                if not response_format.json_schema:
                    raise BadRequestError("JSON schema is required for json_schema response format")
                output_schema = SerializableTaskIO.from_json_schema(response_format.json_schema.schema_)
            case _:
                raise BadRequestError(f"Invalid response format: {response_format.type}")
    else:
        output_schema = RawStringMessageSchema

    if not agent_slug:
        agent_slug = "default"

    return SerializableTaskVariant(
        id="",
        task_schema_id=0,
        task_id=agent_slug,
        input_schema=input_schema,
        output_schema=output_schema,
        name=to_pascal_case(agent_slug),
    )


@router.post(
    "/v1/chat/completions",
    responses={
        200: {
            "content": {
                "text/event-stream": {
                    "schema": OpenAIProxyChatCompletionChunk.model_json_schema(),
                },
                "application/json": {
                    "schema": OpenAIProxyChatCompletionResponse.model_json_schema(),
                },
            },
        },
    },
)
async def chat_completions(
    body: OpenAIProxyChatCompletionRequest,
    group_service: GroupServiceDep,
    storage: StorageDep,
    run_service: RunServiceDep,
    event_router: EventRouterDep,
    request: Request,
    user_org: RequiredUserOrganizationDep,
) -> Response:
    # TODO: content of this function should be split into smaller functions and migrated to a service
    messages = Messages(messages=[m.to_domain() for m in body.messages])
    request_start_time = get_start_time(request)
    # First we need to locate the agent

    try:
        agent_ref = body.extract_references()
    except MissingModelError as e:
        raise await OpenAIProxyService.missing_model_error(e.extras.get("model"))

    if isinstance(agent_ref, EnvironmentRef):
        try:
            deployment = await storage.task_deployments.get_task_deployment(
                agent_ref.agent_id,
                agent_ref.schema_id,
                agent_ref.environment,
            )
        except ObjectNotFoundException:
            raise BadRequestError(
                f"Deployment not found for agent {agent_ref.agent_id}/{agent_ref.schema_id} in "
                f"environment {agent_ref.environment}. Check your deployments "
                f"at {user_org.app_deployments_url(agent_ref.agent_id, agent_ref.schema_id)}",
            )
        properties = deployment.properties
        if variant_id := deployment.properties.task_variant_id:
            variant = await storage.task_version_resource_by_id(
                agent_ref.agent_id,
                variant_id,
            )
        else:
            _logger.warning(
                "No variant id found for deployment, building a new variant",
                extra={"agent_ref": agent_ref},
            )
            variant = _build_variant(messages, agent_ref.agent_id, body.input, body.response_format)

        if body.input is None:
            final_input = messages
        else:
            final_input = body.input
            if messages.messages:
                final_input = {
                    **final_input,
                    INPUT_KEY_MESSAGES: messages.model_dump(mode="json", exclude_none=True)["messages"],
                }
    else:
        raw_variant = _build_variant(messages, agent_ref.agent_id, body.input, body.response_format)
        variant, new_variant_created = await storage.store_task_resource(raw_variant)

        if new_variant_created:
            event_router(
                ProxyAgentCreatedEvent(
                    agent_slug=raw_variant.task_id,
                    task_id=variant.task_id,
                    task_schema_id=variant.task_schema_id,
                ),
            )

        properties = TaskGroupProperties(
            model=agent_ref.model,
            max_tokens=body.max_completion_tokens or body.max_tokens,
            temperature=body.temperature,
            provider=body.workflowai_provider,
            tool_choice=body.worflowai_tool_choice,
        )
        properties.task_variant_id = variant.id

        if body.input:
            # If we have an input, the input schema in the variant must not be the RawMessagesSchema
            # otherwise _build_variant would have raised an error
            # So we can check that the input schema matches and then template the messages as needed
            # We don't remove any extras from the input, we just validate it
            raw_variant.input_schema.enforce(body.input)
            properties.messages = messages.messages
            final_input: dict[str, Any] | Messages = body.input
        else:
            final_input = messages

    if tools := body.domain_tools():
        properties.enabled_tools = tools

    runner, _ = await group_service.sanitize_groups_for_internal_runner(
        task_id=variant.task_id,
        task_schema_id=variant.task_schema_id,
        reference=VersionReference(properties=properties),
        provider_settings=None,
        variant=variant,
        stream_deltas=body.stream is True,
    )

    output_mapper = (
        _raw_string_mapper if variant.output_schema.version == RawStringMessageSchema.version else _output_json_mapper
    )

    return await run_service.run(
        runner=runner,
        task_input=final_input,
        task_run_id=None,
        cache="auto",
        metadata=body.full_metadata(request.headers),
        trigger="user",
        serializer=OpenAIProxyChatCompletionResponse.serializer(
            model=body.model,
            deprecated_function=body.uses_deprecated_functions,
            output_mapper=output_mapper,
        ),
        start_time=request_start_time,
        stream_serializer=OpenAIProxyChatCompletionChunk.stream_serializer(
            model=body.model,
            deprecated_function=body.uses_deprecated_functions,
        )
        if body.stream is True
        else None,
    )
