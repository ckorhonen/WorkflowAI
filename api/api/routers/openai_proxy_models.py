import json
import logging
import re
import time
from collections.abc import Callable, Mapping
from typing import Any, Literal, NamedTuple

from pydantic import BaseModel, ConfigDict, Field
from workflowai import CacheUsage

from core.domain.agent_run import AgentRun
from core.domain.consts import METADATA_KEY_INTEGRATION
from core.domain.errors import BadRequestError
from core.domain.fields.file import File, FileKind
from core.domain.llm_completion import LLMCompletion
from core.domain.message import (
    Message,
    MessageContent,
)
from core.domain.models.models import Model
from core.domain.models.providers import Provider
from core.domain.run_output import RunOutput
from core.domain.task_group_properties import ToolChoice, ToolChoiceFunction
from core.domain.tool import Tool
from core.domain.tool_call import ToolCall, ToolCallRequestWithID
from core.domain.types import AgentOutput
from core.domain.version_environment import VersionEnvironment
from core.providers.base.provider_error import MissingModelError
from core.tools import ToolKind
from core.utils.models.dumps import safe_dump_pydantic_model

# Goal of these models is to be as flexible as possible
# We definitely do not want to reject calls without being sure
# for example if OpenAI decides to change their API or we missed some param in the request
#
# Also all models have extra allowed so we can track extra values that we may have missed

_logger = logging.getLogger(__name__)


class OpenAIAudioInput(BaseModel):
    data: str
    format: str

    def to_domain(self) -> File:
        content_type = self.format
        if "/" not in content_type:
            content_type = f"audio/{content_type}"
        if not self.format or self.data.startswith("https://"):
            # Special case for when the format is not provided or when the data is in fact a URL
            return File(url=self.data, format=FileKind.AUDIO)
        return File(data=self.data, content_type=content_type, format=FileKind.AUDIO)


class OpenAIProxyImageURL(BaseModel):
    url: str
    detail: Literal["low", "high", "auto"] | None = None

    model_config = ConfigDict(extra="allow")


class OpenAIProxyContent(BaseModel):
    type: str
    text: str | None = None
    image_url: OpenAIProxyImageURL | None = None
    input_audio: OpenAIAudioInput | None = None

    def to_domain(self) -> MessageContent:
        match self.type:
            case "text":
                if not self.text:
                    raise BadRequestError("Text content is required")
                return MessageContent(text=self.text)
            case "image_url":
                if not self.image_url:
                    raise BadRequestError("Image URL content is required")
                return MessageContent(file=File(url=self.image_url.url, format=FileKind.IMAGE))
            case "input_audio":
                if not self.input_audio:
                    raise BadRequestError("Input audio content is required")

                return MessageContent(file=self.input_audio.to_domain())
            case _:
                raise BadRequestError(f"Unknown content type: {self.type}", capture=True)

    model_config = ConfigDict(extra="allow")


class OpenAIProxyFunctionCall(BaseModel):
    name: str
    arguments: str | None = None

    model_config = ConfigDict(extra="allow")

    @classmethod
    def from_domain(cls, tool_call: ToolCallRequestWithID):
        return cls(
            name=tool_call.tool_name,
            # The OpenAI SDK does not like None here so we send an empty string instead
            arguments=json.dumps(tool_call.tool_input_dict) if tool_call.tool_input_dict else "",
        )

    def safely_parsed_argument(self) -> dict[str, Any]:
        if not self.arguments:
            return {}
        try:
            return json.loads(self.arguments)
        except json.JSONDecodeError:
            _logger.warning("Failed to parse arguments", extra={"arguments": self.arguments})
            return {"arguments": self.arguments}

    def to_domain(self, id: str):
        return ToolCallRequestWithID(
            id=id,
            tool_name=self.name,
            tool_input_dict=self.safely_parsed_argument(),
        )


class OpenAIProxyFunctionDefinition(BaseModel):
    description: str | None = None
    name: str
    parameters: dict[str, Any]
    strict: bool | None = None

    def to_domain(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            input_schema=self.parameters,
            output_schema={},
            strict=self.strict,
        )

    model_config = ConfigDict(extra="allow")


class OpenAIProxyToolFunction(BaseModel):
    description: str | None = None
    name: str
    parameters: dict[str, Any]
    strict: bool | None = None

    model_config = ConfigDict(extra="allow")


class OpenAIProxyTool(BaseModel):
    type: Literal["function"]
    function: OpenAIProxyToolFunction

    def to_domain(self) -> Tool:
        return Tool(
            name=self.function.name,
            description=self.function.description,
            input_schema=self.function.parameters,
            output_schema={},
            strict=self.function.strict,
        )

    model_config = ConfigDict(extra="allow")


class OpenAIProxyToolCall(BaseModel):
    id: str
    type: Literal["function"] = "function"
    function: OpenAIProxyFunctionCall  # Reusing FunctionCall structure for name/arguments

    @classmethod
    def from_domain(cls, tool_call: ToolCallRequestWithID):
        return cls(
            id=tool_call.id,
            function=OpenAIProxyFunctionCall.from_domain(tool_call),
        )

    def to_domain(self) -> ToolCallRequestWithID:
        return self.function.to_domain(self.id)

    model_config = ConfigDict(extra="allow")


class OpenAIProxyMessage(BaseModel):
    content: list[OpenAIProxyContent] | str | None = None
    name: str | None = None
    role: str

    tool_calls: list[OpenAIProxyToolCall] | None = None
    function_call: OpenAIProxyFunctionCall | None = None  # Deprecated
    tool_call_id: str | None = None

    @classmethod
    def from_run(cls, run: AgentRun, output_mapper: Callable[[AgentOutput], str], deprecated_function: bool):
        return cls(
            role="assistant",
            content=output_mapper(run.task_output),
            tool_calls=[OpenAIProxyToolCall.from_domain(t) for t in run.tool_call_requests]
            if run.tool_call_requests and not deprecated_function
            else None,
            function_call=OpenAIProxyFunctionCall.from_domain(run.tool_call_requests[0])
            if run.tool_call_requests and deprecated_function
            else None,
        )

    def to_domain(self) -> Message:
        if not self.content:
            if self.function_call:
                return Message(
                    content=[MessageContent(tool_call_request=self.function_call.to_domain(""))],
                    role="assistant",
                )
            if self.tool_calls:
                return Message(
                    content=[MessageContent(tool_call_request=t.to_domain()) for t in self.tool_calls],
                    role="assistant",
                )
            raise BadRequestError(
                "Content is required",
                capture=True,
                extras={"messages": safe_dump_pydantic_model(self)},
            )

        if isinstance(self.content, str):
            content = [MessageContent(text=self.content)]
        else:
            content = [c.to_domain() for c in self.content]

        match self.role:
            case "user":
                return Message(content=content, role="user")
            case "tool":
                return Message(
                    content=[
                        MessageContent(
                            tool_call_result=ToolCall(
                                id=self.tool_call_id or "",
                                # TODO: this information is not available
                                # In the message but we could grab it from the previous messages
                                tool_name="",
                                tool_input_dict={},
                                result=self.content,
                            ),
                        ),
                    ],
                    role="user",
                )
            case "assistant":
                return Message(content=content, role="assistant")
            case "system" | "developer":
                # TODO: raising a validation error would mean that the system message is not supported
                return Message(content=content, role="system")
            case _:
                raise BadRequestError(f"Unknown role: {self.role}", capture=True)

    model_config = ConfigDict(extra="allow")


class OpenAIProxyResponseFormat(BaseModel):
    type: str

    class JsonSchema(BaseModel):
        schema_: dict[str, Any] = Field(alias="schema")

    json_schema: JsonSchema | None = None

    model_config = ConfigDict(extra="allow")


class OpenAIProxyStreamOptions(BaseModel):
    include_usage: bool | None = None

    model_config = ConfigDict(extra="allow")


class OpenAIProxyToolChoiceFunction(BaseModel):
    name: str


class OpenAIProxyToolChoice(BaseModel):
    type: Literal["function"]
    function: OpenAIProxyToolChoiceFunction


class OpenAIProxyPredicatedOutput(BaseModel):
    content: str | list[OpenAIProxyContent]
    type: str


class OpenAIProxyWebSearchOptions(BaseModel):
    search_context_size: str

    # TODO:
    user_location: dict[str, Any] | None = None


_UNSUPPORTED_FIELDS = {
    "logit_bias",
    "logprobs",
    "modalities",
    "n",
    "prediction",
    "seed",
    "stop",
    "top_logprobs",
    "web_search_options",
}
_IGNORED_FIELDS = {
    "service_tier",
    "function_call",
    "store",
    "parallel_tool_calls",
}


class EnvironmentRef(NamedTuple):
    """A reference to a deployed environment"""

    agent_id: str
    schema_id: int
    environment: VersionEnvironment


class ModelRef(NamedTuple):
    """A reference to a model with an optional agent id"""

    model: Model
    agent_id: str | None


_agent_schema_env_regex = re.compile(rf"^([^/]+)/#(\d+)/({'|'.join(VersionEnvironment)})$")


class OpenAIProxyChatCompletionRequest(BaseModel):
    messages: list[OpenAIProxyMessage]
    model: str
    frequency_penalty: float | None = Field(None, ge=-2.0, le=2.0)
    function_call: str | OpenAIProxyFunctionCall | None = None
    functions: list[OpenAIProxyFunctionDefinition] | None = None

    logit_bias: dict[str, float] | None = None
    logprobs: bool | None = None

    max_completion_tokens: int | None = None
    max_tokens: int | None = None
    metadata: dict[str, Any] | None = None
    modalities: list[Literal["text", "audio"]] | None = None
    n: int | None = None
    parallel_tool_calls: bool | None = None
    prediction: OpenAIProxyPredicatedOutput | None = None
    presence_penalty: float | None = None
    reasoning_effort: str | None = None
    response_format: OpenAIProxyResponseFormat | None = None

    seed: int | None = None
    service_tier: str | None = None
    stop: str | list[str] | None = None
    store: bool | None = None
    stream: bool | None = None
    stream_options: OpenAIProxyStreamOptions | None = None
    temperature: float = 1  # default OAI temperature differs from own default
    tool_choice: str | OpenAIProxyToolChoice | None = None
    tools: list[OpenAIProxyTool] | None = None
    top_logprobs: int | None = None
    top_p: float | None = None
    user: str | None = None
    web_search_options: OpenAIProxyWebSearchOptions | None = None

    input: dict[str, Any] | None = Field(
        default=None,
        description="An input to template the messages with.This field is not defined by the default OpenAI api."
        "When provided, an input schema is generated and the messages are used as a template.",
    )

    provider: str | None = Field(
        default=None,
        description="A specific provider to use for the request. When provided, multi provider fallback is disabled."
        "The attribute is ignored if the provider is not supported.",
    )

    agent_id: str | None = Field(
        default=None,
        description="The id of the agent to use for the request. If not provided, the default agent is used.",
    )

    environment: str | None = Field(
        default=None,
        description="A reference to an environment where the agent is deployed. It can also be provided in the model "
        "with the format `agent_id/#schema_id/environment`",
    )

    schema_id: int | None = Field(
        default=None,
        description="The agent schema id. Required when using a deployment. It can also be provided in the model "
        "with the format `agent_id/#schema_id/environment`",
    )

    use_cache: CacheUsage | None = None

    model_config = ConfigDict(extra="allow")

    @property
    def uses_deprecated_functions(self) -> bool:
        return self.functions is not None

    def domain_tools(self) -> list[Tool | ToolKind] | None:
        """Returns a tuple of the tools and a boolean indicating if the function call is deprecated"""
        if self.tools:
            return [t.to_domain() for t in self.tools]
        if self.functions:
            return [t.to_domain() for t in self.functions]
        return None

    def full_metadata(self, headers: Mapping[str, Any]) -> dict[str, Any] | None:
        base = self.metadata or {}
        base[METADATA_KEY_INTEGRATION] = "openai_chat_completions"
        if self.user:
            base["user"] = self.user
        if browser_agent := headers.get("user-agent"):
            base["user-agent"] = browser_agent
        return base

    def _check_fields(self):
        set_fields = self.model_fields_set
        for field in _UNSUPPORTED_FIELDS:
            if field in set_fields:
                raise BadRequestError(f"Field {field} is not supported", capture=True)
        for field in _IGNORED_FIELDS:
            _logger.warning(f"Field {field} is ignored by openai proxy")  # noqa: G004

    @property
    def workflowai_provider(self) -> Provider | None:
        if self.provider:
            try:
                return Provider(self.provider)
            except ValueError:
                # Logging for now just in case
                _logger.warning("Received an unsupported provider", extra={"provider": self.provider})
                return None
        return None

    @property
    def worflowai_tool_choice(self) -> ToolChoice | None:
        if not self.tool_choice:
            return None
        if isinstance(self.tool_choice, OpenAIProxyToolChoice):
            return ToolChoiceFunction(name=self.tool_choice.function.name)
        match self.tool_choice:
            case "auto":
                return "auto"
            case "none":
                return "none"
            case "required":
                return "required"
            case _:
                _logger.warning("Received an unsupported tool choice", extra={"tool_choice": self.tool_choice})
                return None

    def _env_from_model_str(self) -> EnvironmentRef | None:
        if match := _agent_schema_env_regex.match(self.model):
            try:
                return EnvironmentRef(
                    agent_id=match.group(1),
                    schema_id=int(match.group(2)),
                    environment=VersionEnvironment(match.group(3)),
                )
            except Exception:
                # That should really not happen. It would be pretty bad because it might mean that our regexp
                # is broken
                _logger.exception(
                    "Model matched regexp but we failed to parse the values",
                    extra={"model": self.model},
                )
        return None

    def _env_from_fields(self, agent_id: str | None, model: Model | None) -> EnvironmentRef | None:
        if not (self.environment or self.schema_id):
            return None
        if not (self.environment and self.schema_id and agent_id):
            raise BadRequestError(
                "When an environment or schema_id is provided, agent_id, environment and schema_id must be provided",
                capture=True,
                extras={"model": self.model, "environment": self.environment, "schema_id": self.schema_id},
            )

        try:
            environment = VersionEnvironment(self.environment)
        except Exception:
            if model:
                # That's ok. It could mean that someone passed an extra body parameter that's also called
                # environment. We can probably ignore it.
                _logger.warning(
                    "Received an invalid environment",
                    extra={"environment": self.environment, "model": self.model},
                )
                return None
            # We don't have a model. Meaning that it's likely a user error
            raise BadRequestError(
                f"Environment {self.environment} is not a valid environment. Valid environments are: {', '.join(VersionEnvironment)}",
                capture=True,
                extras={"model": self.model, "environment": self.environment, "schema_id": self.schema_id},
            )
        return EnvironmentRef(
            agent_id=agent_id,
            schema_id=self.schema_id,
            environment=environment,
        )

    def extract_references(self) -> EnvironmentRef | ModelRef:
        """Extracts the model, agent_id, schema_id and environment from the model string
        and other body optional parameters.
        References can come from either:
        - the model string with a format either "<model>", "<agent_id>/<model>" or "<agent_id>/#<schema_id>/<environment>"
        - the body parameters environment, schema_id and agent_id
        """

        if env := self._env_from_model_str():
            return env

        splits = self.model.split("/")
        agent_id = self.agent_id or (splits[0] if len(splits) > 1 else None)
        # Getting the model from the last component. This is to support cases like litellm that
        # prefix the model string with the provider
        model = Model.from_permissive(splits[-1], reasoning_effort=self.reasoning_effort)

        if env := self._env_from_fields(agent_id, model):
            return env

        if not model:
            raise MissingModelError(model=splits[-1])

        return ModelRef(
            model=model,
            agent_id=agent_id,
        )


# --- Response Models ---


class OpenAIProxyCompletionUsage(BaseModel):
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int

    @classmethod
    def from_domain(cls, completion: LLMCompletion):
        if (
            not completion.usage
            or completion.usage.prompt_token_count is None
            or completion.usage.completion_token_count is None
        ):
            return None

        return cls(
            completion_tokens=int(completion.usage.completion_token_count),
            prompt_tokens=int(completion.usage.prompt_token_count),
            total_tokens=int(completion.usage.prompt_token_count + completion.usage.completion_token_count),
        )


class OpenAIProxyChatCompletionChoice(BaseModel):
    finish_reason: Literal["stop", "length", "tool_calls", "content_filter", "function_call"]
    index: int
    message: OpenAIProxyMessage

    @classmethod
    def from_domain(cls, run: AgentRun, output_mapper: Callable[[AgentOutput], str], deprecated_function: bool):
        msg = OpenAIProxyMessage.from_run(run, output_mapper, deprecated_function)
        if run.tool_call_requests:
            finish_reason = "function_call" if deprecated_function else "tool_calls"
        else:
            finish_reason = "stop"

        return cls(
            finish_reason=finish_reason,
            index=0,
            message=msg,
        )


class OpenAIProxyChatCompletionResponse(BaseModel):
    id: str
    choices: list[OpenAIProxyChatCompletionChoice]
    created: int  # Unix timestamp
    model: str
    system_fingerprint: str | None = None
    object: Literal["chat.completion"] = "chat.completion"
    usage: OpenAIProxyCompletionUsage | None = None

    cost_usd: float | None = Field(description="The cost of the completion in USD, WorkflowAI specific")

    @classmethod
    def from_domain(
        cls,
        run: AgentRun,
        output_mapper: Callable[[AgentOutput], str],
        model: str,
        deprecated_function: bool,
    ):
        return cls(
            id=f"{run.task_id}/{run.id}",
            choices=[OpenAIProxyChatCompletionChoice.from_domain(run, output_mapper, deprecated_function)],
            created=int(run.created_at.timestamp()),
            model=model,
            cost_usd=run.cost_usd,
            usage=OpenAIProxyCompletionUsage.from_domain(run.llm_completions[-1]) if run.llm_completions else None,
        )

    @classmethod
    def serializer(cls, model: str, deprecated_function: bool, output_mapper: Callable[[Any], str]):
        def _serializer(run: AgentRun):
            return cls.from_domain(run, output_mapper, model, deprecated_function)

        return _serializer


class OpenAIProxyChatCompletionChunkDelta(BaseModel):
    content: str | None = None
    function_call: OpenAIProxyFunctionCall | None = None  # Deprecated
    tool_calls: list[OpenAIProxyToolCall] | None = None
    role: Literal["user", "assistant", "system", "tool"] | None = None

    @classmethod
    def from_domain(cls, output: RunOutput, deprecated_function: bool):
        if not output.delta and not output.tool_call_requests:
            return None
        return cls(
            content=output.delta,
            function_call=OpenAIProxyFunctionCall.from_domain(output.tool_call_requests[0])
            if deprecated_function and output.tool_call_requests
            else None,
            tool_calls=[OpenAIProxyToolCall.from_domain(t) for t in output.tool_call_requests]
            if output.tool_call_requests and not deprecated_function
            else None,
        )


class OpenAIProxyChatCompletionChunkChoice(BaseModel):
    delta: OpenAIProxyChatCompletionChunkDelta
    finish_reason: Literal["stop", "length", "tool_calls", "content_filter", "function_call"] | None = None
    index: int


class OpenAIProxyChatCompletionChunk(BaseModel):
    id: str
    choices: list[OpenAIProxyChatCompletionChunkChoice]
    created: int
    model: str
    system_fingerprint: str | None = None
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    usage: OpenAIProxyCompletionUsage | None = None

    @classmethod
    def from_domain(cls, id: str, output: RunOutput, model: str, deprecated_function: bool):
        chunk_delta = OpenAIProxyChatCompletionChunkDelta.from_domain(output, deprecated_function)
        if not chunk_delta:
            return None
        return cls(
            id=id,
            created=int(time.time()),
            model=model,
            choices=[OpenAIProxyChatCompletionChunkChoice(delta=chunk_delta, finish_reason="stop", index=0)],
        )

    @classmethod
    def stream_serializer(cls, model: str, deprecated_function: bool):
        def _serializer(id: str, output: RunOutput):
            return cls.from_domain(id, output, model=model, deprecated_function=deprecated_function)

        return _serializer
