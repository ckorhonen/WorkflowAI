from collections.abc import Callable
from json import JSONDecodeError
from typing import Any, AsyncGenerator, override

from httpx import Response

from core.domain.llm_completion import LLMCompletion
from core.domain.message import Message
from core.domain.models.models import Model
from core.domain.models.providers import Provider
from core.domain.structured_output import StructuredOutput
from core.domain.tool import Tool
from core.providers.base.httpx_provider_base import HTTPXProviderBase
from core.providers.base.models import RawCompletion, StandardMessage
from core.providers.base.provider_options import ProviderOptions
from core.providers.base.utils import get_provider_config_env
from core.providers.openai_image.openai_image_config import OpenAIImageConfig
from core.providers.openai_image.openai_image_domain import OpenAIImageRequest, OpenAIImageResponse
from core.runners.workflowai.utils import FileWithKeyPath


class OpenAIImageProvider(HTTPXProviderBase[OpenAIImageConfig, OpenAIImageRequest]):
    @override
    def default_model(self) -> Model:
        return Model.GPT_IMAGE_1

    @classmethod
    @override
    def name(cls) -> Provider:
        return Provider.OPEN_AI_IMAGE

    @classmethod
    @override
    def required_env_vars(cls) -> list[str]:
        return ["OPENAI_API_KEY"]

    @classmethod
    @override
    def _default_config(cls, index: int) -> OpenAIImageConfig:
        return OpenAIImageConfig(
            api_key=get_provider_config_env("OPENAI_API_KEY", index),
        )

    @override
    def is_streamable(self, model: Model, enabled_tools: list[Tool] | None = None) -> bool:
        return False

    @classmethod
    def requires_downloading_file(cls, file: FileWithKeyPath, model: Model) -> bool:
        return True

    @override
    async def _extract_and_log_rate_limits(self, response: Response, options: ProviderOptions):
        await self._log_rate_limit_remaining(
            "requests",
            remaining=response.headers.get("x-ratelimit-remaining-requests"),
            total=response.headers.get("x-ratelimit-limit-requests"),
            options=options,
        )
        await self._log_rate_limit_remaining(
            "tokens",
            remaining=response.headers.get("x-ratelimit-remaining-tokens"),
            total=response.headers.get("x-ratelimit-limit-tokens"),
            options=options,
        )

    @override
    def _compute_prompt_token_count(
        self,
        messages: list[dict[str, Any]],
        model: Model,
    ) -> float:
        raise NotImplementedError("_compute_prompt_token_count should not be called for OpenAI Image")

    @override
    @classmethod
    def _compute_completion_token_count(
        cls,
        response: str,
        model: Model,
    ) -> int:
        raise NotImplementedError("_compute_completion_token_count should not be called for OpenAI Image")

    # TODO: deprecate this method
    @override
    def _compute_prompt_image_count(
        self,
        messages: list[dict[str, Any]],
    ) -> int:
        return 0

    @override
    async def _compute_prompt_audio_token_count(
        self,
        messages: list[dict[str, Any]],
    ) -> tuple[float, float | None]:
        return 0, None

    @override
    @classmethod
    def standardize_messages(cls, messages: list[dict[str, Any]]) -> list[StandardMessage]:
        return []

    @override
    async def _prepare_completion(
        self,
        messages: list[Message],
        options: ProviderOptions,
        stream: bool,
    ) -> tuple[OpenAIImageRequest, LLMCompletion]:
        prompt = "\n".join([m.content for m in messages])

        raw = LLMCompletion(
            messages=[{"role": "user", "content": prompt}],
            usage=self._initial_usage(messages),
            provider=self.name(),
        )
        req = OpenAIImageRequest(prompt=prompt, n=1, image=None, mask=None, model=options.model)

        return req, raw

    @override
    async def _execute_request(self, request: OpenAIImageRequest, options: ProviderOptions) -> Response:
        url = (
            "https://api.openai.com/v1/images/edits"
            if request.is_edit_request
            else "https://api.openai.com/v1/images/generations"
        )

        async with self._open_client(url) as client:
            return await client.post(
                url,
                # Probably have to send the mask and image as files
                headers={"Authorization": f"Bearer {self._config.api_key}"},
                json=request.model_dump(mode="json", exclude_none=True, by_alias=True),
                timeout=options.timeout,
            )

    @override
    def _parse_response(
        self,
        response: Response,
        output_factory: Callable[[str, bool], StructuredOutput],
        raw_completion: RawCompletion,
        request: OpenAIImageRequest,
    ):
        try:
            raw = response.json()
        except JSONDecodeError:
            raw_completion.response = response.text
            res = self._unknown_error(response)
            res.set_response(response)
            raise res
        response_model = OpenAIImageResponse.model_validate(raw)
        content_type = request.content_type
        files = [d.to_file(content_type) for d in response_model.data]
        return StructuredOutput(output={}, files=files)

    @override
    def _single_stream(
        self,
        request: OpenAIImageRequest,
        output_factory: Callable[[str, bool], StructuredOutput],
        partial_output_factory: Callable[[Any], StructuredOutput],
        raw_completion: RawCompletion,
        options: ProviderOptions,
    ) -> AsyncGenerator[StructuredOutput, None]:
        raise NotImplementedError("_single_stream is not supported for OpenAI Image")
