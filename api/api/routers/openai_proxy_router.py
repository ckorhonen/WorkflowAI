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
from core.domain.task_io import RawJSONSchema, RawStringSchema, SerializableTaskIO
from core.domain.task_variant import SerializableTaskVariant
from core.domain.types import AgentOutput
from core.domain.version_reference import VersionReference

router = APIRouter(prefix="", tags=["openai"])


_raw_messages_input_schema = SerializableTaskIO.from_model(Messages)


_model_mapping = {
    "gpt-4o": Model.GPT_4O_LATEST,
}


def _agent_and_model(model: str) -> tuple[str, Model]:
    agent_and_model = model.split("/")
    if len(agent_and_model) > 2:
        raise BadRequestError(f"Invalid model: {model}")

    if len(agent_and_model) == 1:
        agent_name = "openai-proxy-agent"
        model_str = agent_and_model[0]
    else:
        agent_name = agent_and_model[0]
        model_str = agent_and_model[1]

    if model_str in _model_mapping:
        model = _model_mapping[model_str]
    else:
        try:
            model = Model(model_str)
        except ValueError:
            raise BadRequestError(f"Model does not exist {model}")

    return agent_name, model


def _raw_string_mapper(output: Any) -> str:
    return output


def _output_json_mapper(output: AgentOutput) -> str:
    return json.dumps(output)


def _build_variant(agent_slug: str, response_format: OpenAIProxyResponseFormat | None):
    input_schema = _raw_messages_input_schema

    if response_format:
        match response_format.type:
            case "text":
                output_schema = RawStringSchema
                mapper = _raw_string_mapper
            case "json_object":
                output_schema = RawJSONSchema
                mapper = _output_json_mapper
            case "json_schema":
                if not response_format.json_schema:
                    raise BadRequestError("JSON schema is required for json_schema response format")
                output_schema = SerializableTaskIO.from_json_schema(response_format.json_schema.schema_)
                mapper = _output_json_mapper
            case _:
                raise BadRequestError(f"Invalid response format: {response_format.type}")
    else:
        output_schema = RawStringSchema
        mapper = _raw_string_mapper

    return SerializableTaskVariant(
        id="",
        task_schema_id=0,
        task_id=agent_slug,
        input_schema=input_schema,
        output_schema=output_schema,
        name=agent_slug,
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
    request_start_time = get_start_time(request)
    # First we need to locate the agent
    agent_slug, model = _agent_and_model(body.model)
    raw_variant, output_mapper = _build_variant(agent_slug, body.response_format)
    variant, _ = await storage.store_task_resource(raw_variant)

    tool_calls, deprecated_function = body.domain_tools()
    properties = TaskGroupProperties(model=model, enabled_tools=tool_calls)
    properties.task_variant_id = variant.id

    runner, _ = await group_service.sanitize_groups_for_internal_runner(
        task_id=variant.task_id,
        task_schema_id=variant.task_schema_id,
        reference=VersionReference(properties=properties),
        provider_settings=None,
        variant=variant,
    )

    return await run_service.run(
        runner=runner,
        task_input=Messages(messages=[m.to_domain() for m in body.messages]),
        task_run_id=None,
        stream_serializer=None,
        cache="auto",
        metadata=body.metadata,
        trigger="user",
        serializer=lambda run: OpenAIProxyChatCompletionResponse.from_domain(
            run,
            output_mapper,
            body.model,
            deprecated_function,
        ),
        start_time=request_start_time,
    )
