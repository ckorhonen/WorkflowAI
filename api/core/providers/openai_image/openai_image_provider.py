import io
import logging
from base64 import b64decode
from collections.abc import Callable
from json import JSONDecodeError
from typing import Any, AsyncGenerator, override

from httpx import Response
from pydantic import ValidationError

from core.domain.fields.file import File
from core.domain.fields.image_options import ImageOptions
from core.domain.llm_completion import LLMCompletion
from core.domain.message import MessageDeprecated
from core.domain.models.models import Model
from core.domain.models.providers import Provider
from core.domain.structured_output import StructuredOutput
from core.domain.tool import Tool
from core.providers.base.httpx_provider_base import HTTPXProviderBase
from core.providers.base.models import RawCompletion, StandardMessage
from core.providers.base.provider_error import ContentModerationError, ProviderError, UnknownProviderError
from core.providers.base.provider_options import ProviderOptions
from core.providers.base.utils import get_provider_config_env
from core.providers.openai_image.openai_image_config import OpenAIImageConfig
from core.providers.openai_image.openai_image_domain import OpenAIImageError, OpenAIImageRequest, OpenAIImageResponse
from core.runners.workflowai.templates import TemplateName

_logger = logging.getLogger(__name__)


class OpenAIImageProvider(HTTPXProviderBase[OpenAIImageConfig, OpenAIImageRequest]):
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
    def requires_downloading_file(cls, file: File, model: Model) -> bool:
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
        messages: list[MessageDeprecated],
        options: ProviderOptions,
        stream: bool,
    ) -> tuple[OpenAIImageRequest, LLMCompletion]:
        prompt = "\n".join([m.content for m in messages])

        raw = LLMCompletion(
            messages=[{"role": "user", "content": prompt}],
            usage=self._initial_usage(messages),
            provider=self.name(),
        )
        image_options = messages[0].image_options or ImageOptions()
        req = OpenAIImageRequest.build(
            prompt=prompt,
            image_options=image_options,
            model=options.model,
        )

        images: list[File] = []
        for message in messages:
            if message.files:
                for file in message.files:
                    if not file.is_image:
                        _logger.warning("Non image file found in message, ignoring")
                        continue
                    if not file.data:
                        _logger.warning("Image file has no data, ignoring")
                        continue
                    images.append(file)
        req.images = images or None
        req.mask = image_options.mask

        return req, raw

    @classmethod
    def _httpx_files(cls, images: list[File]):
        for idx, image in enumerate(images):
            if not image.data:
                continue
            if not image.content_type:
                continue
            yield (f"{idx}{image.get_extension()}", io.BytesIO(b64decode(image.data)), image.content_type)

    @override
    async def _execute_request(self, request: OpenAIImageRequest, options: ProviderOptions) -> Response:
        data = request.model_dump(mode="json", exclude_none=True, by_alias=True, exclude={"images", "mask"})
        if request.images:
            url = "https://api.openai.com/v1/images/edits"
            kwargs: dict[str, Any] = {"data": data}

            files: list[Any] = []
            for f in self._httpx_files(request.images):
                files.append(("image[]", f))  # noqa: PERF401
            if request.mask:
                for f in self._httpx_files([request.mask]):
                    files.append(("mask[]", f))  # noqa: PERF401
            kwargs["files"] = files

        else:
            url = "https://api.openai.com/v1/images/generations"
            kwargs = {"json": data}

        async with self._open_client(url) as client:
            response = await client.post(
                url,
                # Probably have to send the mask and image as files
                headers={"Authorization": f"Bearer {self._config.api_key}"},
                timeout=self.timeout_or_default(options.timeout),
                **kwargs,
            )
            response.raise_for_status()
            return response

    @override
    def sanitize_template(self, template: TemplateName):
        # Forcing the absence of schema.
        # Imagen behaves weirdly when the schema is present.
        return TemplateName.V2_NO_INPUT_OR_OUTPUT_SCHEMA

    @override
    def _unknown_error(self, response: Response) -> ProviderError:
        try:
            raw = response.json()
            error = OpenAIImageError.model_validate(raw)
        except (JSONDecodeError, ValidationError):
            _logger.exception("Failed to parse OpenAI Image response as JSON")
            return super()._unknown_error(response)

        if error.error.code == "moderation_blocked":
            return ContentModerationError(
                error.error.message or "The image was blocked by OpenAI's moderation system.",
            )
        return UnknownProviderError(
            error.error.message or "An unknown error occurred while generating the image.",
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
        if response_model.usage:
            response_model.usage.assign(raw_completion.usage)
        content_type = request.content_type
        files = [d.to_file(content_type) for d in response_model.data]
        return StructuredOutput(output=None, files=files)

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
