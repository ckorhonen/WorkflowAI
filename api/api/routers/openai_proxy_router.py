import json
from typing import Any

from fastapi import APIRouter, Request, Response

from api.dependencies.services import GroupServiceDep, RunServiceDep
from api.dependencies.storage import StorageDep
from api.routers.openai_proxy_models import (
    OpenAIProxyChatCompletionChunk,
    OpenAIProxyChatCompletionRequest,
    OpenAIProxyChatCompletionResponse,
    OpenAIProxyResponseFormat,
)
from api.utils import get_start_time
from core.domain.errors import BadRequestError
from core.domain.message import Messages
from core.domain.models.models import Model
from core.domain.task_group_properties import TaskGroupProperties
from core.domain.task_io import RawJSONMessageSchema, RawMessagesSchema, RawStringMessageSchema, SerializableTaskIO
from core.domain.task_variant import SerializableTaskVariant
from core.domain.types import AgentOutput
from core.domain.version_reference import VersionReference
from core.utils.schemas import schema_from_data
from core.utils.strings import to_pascal_case
from core.utils.templates import extract_variable_schema

router = APIRouter(prefix="", tags=["openai"])


_model_mapping = {
    "gpt-4o": Model.GPT_4O_LATEST,
}


def _parse_model(model: str) -> Model:
    if model in _model_mapping:
        return _model_mapping[model]

    # We try to parse the model as a Model
    try:
        return Model(model)
    except ValueError:
        pass

    # Then we check if it's a unversioned model, called "latest" here
    try:
        return Model(model + "-latest")
    except ValueError:
        pass

    raise BadRequestError(f"Model does not exist {model}")


def _agent_and_model(model: str) -> tuple[str | None, Model]:
    agent_and_model = model.split("/")
    if len(agent_and_model) > 2:
        raise BadRequestError(f"Invalid model: {model}")

    if len(agent_and_model) == 1:
        agent_name = None
        model_str = agent_and_model[0]
    else:
        agent_name = agent_and_model[0]
        model_str = agent_and_model[1]

    return agent_name, _parse_model(model_str)


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
    return SerializableTaskIO.from_json_schema(schema_from_template, streamline=True)


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
                mapper = _raw_string_mapper
            case "json_object":
                output_schema = RawJSONMessageSchema
                mapper = _output_json_mapper
            case "json_schema":
                if not response_format.json_schema:
                    raise BadRequestError("JSON schema is required for json_schema response format")
                output_schema = SerializableTaskIO.from_json_schema(response_format.json_schema.schema_)
                mapper = _output_json_mapper
            case _:
                raise BadRequestError(f"Invalid response format: {response_format.type}")
    else:
        output_schema = RawStringMessageSchema
        mapper = _raw_string_mapper

    if not agent_slug:
        agent_slug = "default"

    return SerializableTaskVariant(
        id="",
        task_schema_id=0,
        task_id=agent_slug,
        input_schema=input_schema,
        output_schema=output_schema,
        name=to_pascal_case(agent_slug),
    ), mapper


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
    request: Request,
) -> Response:
    messages = Messages(messages=[m.to_domain() for m in body.messages])
    request_start_time = get_start_time(request)
    # First we need to locate the agent
    agent_slug, model = _agent_and_model(body.model)
    raw_variant, output_mapper = _build_variant(messages, agent_slug, body.input, body.response_format)
    variant, _ = await storage.store_task_resource(raw_variant)

    tool_calls, deprecated_function = body.domain_tools()
    properties = TaskGroupProperties(
        model=model,
        enabled_tools=tool_calls,
        max_tokens=body.max_completion_tokens or body.max_tokens,
        temperature=body.temperature,
        provider=body.workflowai_provider,
        tool_choice=body.worflowai_tool_choice,
    )

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

    properties.task_variant_id = variant.id

    runner, _ = await group_service.sanitize_groups_for_internal_runner(
        task_id=variant.task_id,
        task_schema_id=variant.task_schema_id,
        reference=VersionReference(properties=properties),
        provider_settings=None,
        variant=variant,
        stream_deltas=body.stream is True,
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
            deprecated_function=deprecated_function,
            output_mapper=output_mapper,
        ),
        start_time=request_start_time,
        stream_serializer=OpenAIProxyChatCompletionChunk.stream_serializer(
            model=body.model,
            deprecated_function=deprecated_function,
        )
        if body.stream is True
        else None,
    )
