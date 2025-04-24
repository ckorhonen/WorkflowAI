from abc import abstractmethod
from collections.abc import Callable
from json import JSONDecodeError
from typing import Any, AsyncGenerator, AsyncIterator, Generic, NamedTuple, TypeVar

from httpx import ReadTimeout, RemoteProtocolError, Response
from pydantic import BaseModel
from typing_extensions import override

from core.domain.errors import (
    ContentModerationError,
    FailedGenerationError,
    InternalError,
    JSONSchemaValidationError,
    ProviderError,
    ProviderInternalError,
    ReadTimeOutError,
)
from core.domain.fields.internal_reasoning_steps import InternalReasoningStep
from core.domain.llm_completion import LLMCompletion
from core.domain.llm_usage import LLMUsage
from core.domain.message import Message
from core.domain.models import Model
from core.domain.structured_output import StructuredOutput
from core.domain.tool_call import ToolCallRequestWithID
from core.providers.base.abstract_provider import ProviderConfigVar, RawCompletion
from core.providers.base.client_pool import ClientPool
from core.providers.base.httpx_provider_base import HTTPXProviderBase
from core.providers.base.provider_options import ProviderOptions
from core.providers.base.streaming_context import StreamingContext, ToolCallRequestBuffer
from core.utils.background import add_background_task
from core.utils.dicts import InvalidKeyPathError, set_at_keypath_str
from core.utils.json_utils import extract_json_str
from core.utils.streams import standard_wrap_sse

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)

shared_client_pool = ClientPool()


class ParsedResponse(NamedTuple):
    content: str
    reasoning_steps: str | None = None
    # TODO: switch to tool call request
    tool_calls: list[ToolCallRequestWithID] | None = None


class HTTPXProvider(HTTPXProviderBase[ProviderConfigVar, dict[str, Any]], Generic[ProviderConfigVar, ResponseModel]):
    @abstractmethod
    def _build_request(self, messages: list[Message], options: ProviderOptions, stream: bool) -> BaseModel:
        pass

    @abstractmethod
    async def _request_headers(self, request: dict[str, Any], url: str, model: Model) -> dict[str, str]:
        pass

    @abstractmethod
    def _request_url(self, model: Model, stream: bool) -> str:
        pass

    @abstractmethod
    def _response_model_cls(self) -> type[ResponseModel]:
        pass

    @abstractmethod
    def _extract_content_str(self, response: ResponseModel) -> str:
        pass

    def _extract_reasoning_steps(self, response: ResponseModel) -> list[InternalReasoningStep] | None:
        return None

    def _extract_usage(self, response: ResponseModel) -> LLMUsage | None:
        return None

    @classmethod
    def _extract_native_tool_calls(cls, response: ResponseModel) -> list[ToolCallRequestWithID]:
        # Method is overriden in subclasses that support native tool calls
        return []

    @abstractmethod
    def _extract_stream_delta(
        self,
        sse_event: bytes,
        raw_completion: RawCompletion,
        tool_call_request_buffer: dict[int, ToolCallRequestBuffer],
    ) -> ParsedResponse:
        pass

    def _raw_prompt(self, request_json: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract the raw prompt from the request JSON"""
        return request_json["messages"]

    @override
    def _parse_response(
        self,
        response: Response,
        output_factory: Callable[[str, bool], StructuredOutput],
        raw_completion: RawCompletion,
        request: dict[str, Any],
    ) -> StructuredOutput:
        try:
            raw = response.json()
        except JSONDecodeError:
            raw_completion.response = response.text
            res = self._unknown_error(response)
            res.set_response(response)
            raise res
        response_model = self._response_model_cls().model_validate(raw)
        # Initialize content_str with the response text so that
        # if we raise an error, we have the original response text
        content_str = response.text
        native_tool_calls = []
        reasoning_steps = []
        try:
            native_tool_calls = self._extract_native_tool_calls(response_model)
            reasoning_steps = self._extract_reasoning_steps(response_model)
            content_str = self._extract_content_str(response_model)
            content_str = extract_json_str(content_str)
        except ProviderError as e:
            # If the error is already a provider error, we just re-raise it
            raw_completion.response = content_str
            e.set_response(response)
            raise e
        except Exception as e:
            raw_completion.response = content_str

            if len(native_tool_calls) == 0:
                raise self._invalid_json_error(response, e, content_str) from e
            # If there are native tool calls, we don't care if the text answer is empty or a valid JSON or not.
        finally:
            usage = self._extract_usage(response_model)
            raw_completion.response = content_str
            if usage:
                raw_completion.usage = usage

        return self._build_structured_output(
            output_factory,
            content_str,
            reasoning_steps,
            native_tools_calls=native_tool_calls,
        )

    @classmethod
    def _initial_usage(cls, messages: list[Message]) -> LLMUsage:
        image_count = 0
        has_audio = False
        for m in messages:
            if m.files:
                for f in m.files:
                    if f.is_image or f.is_pdf:
                        image_count += 1
                    if f.is_audio:
                        has_audio = True
        usage = LLMUsage(prompt_image_count=image_count)
        if not has_audio:
            usage.prompt_audio_duration_seconds = 0
            usage.prompt_audio_token_count = 0
        return usage

    @override
    async def _prepare_completion(self, messages: list[Message], options: ProviderOptions, stream: bool):
        request = self._build_request(messages, options, stream=stream)
        body = request.model_dump(mode="json", exclude_none=True, by_alias=True)

        raw = LLMCompletion(
            messages=self._raw_prompt(body),
            usage=self._initial_usage(messages),
            provider=self.name(),
        )

        return body, raw

    @override
    async def _execute_request(self, request: dict[str, Any], options: ProviderOptions) -> Response:
        url = self._request_url(model=options.model, stream=False)
        headers = await self._request_headers(request, url, options.model)

        async with self._open_client(url) as client:
            return await client.post(
                url,
                json=request,
                headers=headers,
                timeout=options.timeout,
            )

    async def wrap_sse(self, raw: AsyncIterator[bytes], termination_chars: bytes = b"\n\n"):
        async for chunk in standard_wrap_sse(raw, termination_chars, self.logger):
            yield chunk

    @classmethod
    def _partial_structured_output(
        cls,
        partial_output_factory: Callable[[Any], StructuredOutput],
        data: Any,
        reasoning_steps: list[InternalReasoningStep] | None = None,
    ):
        partial = partial_output_factory(data)
        if reasoning_steps:
            partial = partial._replace(reasoning_steps=reasoning_steps)
        return partial

    @classmethod
    def _build_structured_output(
        cls,
        output_factory: Callable[[str, bool], StructuredOutput],
        raw: str,
        reasoning_steps: list[InternalReasoningStep] | None = None,
        native_tools_calls: list[ToolCallRequestWithID] | None = None,
    ):
        try:
            output = output_factory(raw, False)
        except JSONSchemaValidationError as e:
            if not native_tools_calls:
                raise e
            # When there is a native tool call, we can afford having a JSONSchemaValidationError,
            # ex: when the models returns a raw "Let me use the @search-google tool to answer the question"  in the completion
            # This happens quite often with Claude models.
            output = StructuredOutput(output={})
        if reasoning_steps:
            output = output._replace(reasoning_steps=reasoning_steps)
        if native_tools_calls:
            output = output._replace(tool_calls=native_tools_calls + (output.tool_calls or []))
        return output

    def _failed_generation_error_wrapper(self, raw_completion: str, error_msg: str, retry: bool = False):
        # Check for content moderation rejection patterns in the response text.
        # Some providers (e.g. Bedrock) may return HTTP 200 but indicate content
        # rejection through apologetic messages in the response text.
        moderation_patterns = ["inappropriate", "offensive"]
        if "apologize" in raw_completion.lower() and any(
            pattern in raw_completion.lower() for pattern in moderation_patterns
        ):
            return ContentModerationError(retry=retry, provider_error=raw_completion)
        return FailedGenerationError(msg=error_msg, raw_completion=raw_completion, retry=retry)

    def _handle_chunk_output(self, context: StreamingContext, content: str) -> bool:
        updates = context.streamer.process_chunk(content)
        if not updates:
            return False

        for keypath, value in updates:
            try:
                set_at_keypath_str(context.agg_output, keypath, value)
            except InvalidKeyPathError as e:
                raise InternalError(
                    f"Invalid keypath in stream: {e}",
                    extras={
                        "aggregate": context.streamer.aggregate,
                        "output": context.agg_output,
                        "keypath": keypath,
                        "value": value,
                    },
                ) from e
        return True

    def _handle_chunk_reasoning_steps(self, context: StreamingContext, extracted: str | None) -> bool:
        if not extracted:
            return False
        # TODO: we currently do not handle having a provider return multiple reasoning steps
        if not context.reasoning_steps:
            context.reasoning_steps = [InternalReasoningStep(explaination="")]
        context.reasoning_steps[0].append_explanation(extracted)
        return True

    def _handle_chunk_tool_calls(
        self,
        context: StreamingContext,
        extracted: list[ToolCallRequestWithID] | None,
    ) -> bool:
        if extracted:
            if not context.tool_calls:
                context.tool_calls = []
            context.tool_calls.extend(extracted)
        # Tool calls are only yielded once the stream is done
        return False

    def _handle_chunk(self, context: StreamingContext, chunk: bytes) -> bool:
        """Handles a chunk and returns true if there was an update"""
        delta = self._extract_stream_delta(chunk, context.raw_completion, context.tool_call_request_buffer)
        if not delta:
            return False

        should_yield = self._handle_chunk_output(context, delta.content)
        should_yield |= self._handle_chunk_reasoning_steps(context, delta.reasoning_steps)
        should_yield |= self._handle_chunk_tool_calls(context, delta.tool_calls)
        return should_yield

    @override
    async def _single_stream(  # noqa: C901
        self,
        request: dict[str, Any],
        output_factory: Callable[[str, bool], StructuredOutput],
        partial_output_factory: Callable[[Any], StructuredOutput],
        raw_completion: RawCompletion,
        options: ProviderOptions,
    ) -> AsyncGenerator[StructuredOutput, None]:
        streaming_context: StreamingContext | None = None
        try:
            url = self._request_url(model=options.model, stream=True)
            headers = await self._request_headers(request=request, url=url, model=options.model)
            async with self._open_client(url) as client:
                async with client.stream(
                    "POST",
                    url,
                    json=request,
                    headers=headers,
                    timeout=options.timeout,
                ) as response:
                    add_background_task(self._extract_and_log_rate_limits(response, options))
                    if not response.is_success:
                        # We need to read the response to get the error message
                        await response.aread()
                        response.raise_for_status()

                    streaming_context = StreamingContext(raw_completion)
                    async for chunk in self.wrap_sse(response.aiter_bytes()):
                        should_yield = self._handle_chunk(streaming_context, chunk)

                        if should_yield:
                            yield self._partial_structured_output(
                                partial_output_factory,
                                streaming_context.agg_output,
                                streaming_context.reasoning_steps,
                            )

                    # TODO: we should be using the streamed JSON here
                    try:
                        json_str = extract_json_str(streaming_context.streamer.raw_completion)
                    except ValueError:
                        if not streaming_context.tool_calls:
                            raise self._failed_generation_error_wrapper(
                                streaming_context.streamer.raw_completion,
                                "Generation does not contain a valid JSON",
                                retry=True,
                            )
                        json_str = "{}"
                    try:
                        yield self._build_structured_output(
                            output_factory,
                            json_str,
                            streaming_context.reasoning_steps,
                            streaming_context.tool_calls,
                        )
                    except JSONSchemaValidationError as e:
                        raise self._failed_generation_error_wrapper(
                            streaming_context.streamer.raw_completion,
                            str(e),
                        )
        except ReadTimeout:
            raise ReadTimeOutError(retry=True, retry_after=10)
        except RemoteProtocolError:
            raise ProviderInternalError(msg="Provider has disconnected without sending a response.", retry_after=10)
        finally:
            raw_completion.response = streaming_context.streamer.raw_completion if streaming_context else None
