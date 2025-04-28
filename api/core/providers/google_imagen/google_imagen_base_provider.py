import logging
from abc import abstractmethod
from collections.abc import Callable
from json import JSONDecodeError
from typing import Any, AsyncGenerator, override

from httpx import Response

from core.domain.fields.image_options import ImageOptions
from core.domain.llm_completion import LLMCompletion
from core.domain.message import Message
from core.domain.models.models import Model
from core.domain.structured_output import StructuredOutput
from core.domain.tool import Tool
from core.providers.base.abstract_provider import ProviderConfigVar
from core.providers.base.httpx_provider_base import HTTPXProviderBase
from core.providers.base.models import RawCompletion, StandardMessage
from core.providers.base.provider_options import ProviderOptions
from core.providers.google_imagen.google_imagen_domain import GoogleImagenRequest, GoogleImagenResponse
from core.runners.workflowai.templates import TemplateName
from core.runners.workflowai.utils import FileWithKeyPath

_logger = logging.getLogger(__name__)


class GoogleImagenBaseProvider(HTTPXProviderBase[ProviderConfigVar, GoogleImagenRequest]):
    @override
    def default_model(self) -> Model:
        return Model.IMAGEN_3_0_001

    @override
    def is_streamable(self, model: Model, enabled_tools: list[Tool] | None = None) -> bool:
        return False

    @classmethod
    def requires_downloading_file(cls, file: FileWithKeyPath, model: Model) -> bool:
        return True

    @override
    def _compute_prompt_token_count(
        self,
        messages: list[dict[str, Any]],
        model: Model,
    ) -> float:
        return 0

    @override
    @classmethod
    def _compute_completion_token_count(
        cls,
        response: str,
        model: Model,
    ) -> int:
        return 0

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
    def sanitize_template(self, template: TemplateName):
        # Forcing the absence of schema.
        # Imagen behaves weirdly when the schema is present.
        return TemplateName.V2_NO_INPUT_OR_OUTPUT_SCHEMA

    @override
    async def _prepare_completion(
        self,
        messages: list[Message],
        options: ProviderOptions,
        stream: bool,
    ) -> tuple[GoogleImagenRequest, LLMCompletion]:
        prompt = "\n".join([m.content for m in messages])

        raw = LLMCompletion(
            messages=[{"role": "user", "content": prompt}],
            usage=self._initial_usage(messages),
            provider=self.name(),
        )
        image_options = messages[0].image_options or ImageOptions()
        instance = GoogleImagenRequest.Instance(prompt=prompt)

        for message in messages:
            if message.files:
                instance.referenceImages = []
                for file in message.files:
                    if not file.is_image:
                        _logger.warning("Non image file found in message, ignoring")
                        continue
                    if not file.data:
                        _logger.warning("Image file has no data, ignoring")
                        continue
                    instance.referenceImages.append(
                        GoogleImagenRequest.Instance.ReferenceImage(
                            referenceType="REFERENCE_TYPE_RAW",
                            referenceId=0,
                            referenceImage=GoogleImagenRequest.Instance.ReferenceImage.Image(
                                bytesBase64Encoded=file.data,
                            ),
                        ),
                    )

        if image_options.mask and instance.referenceImages and image_options.mask.data:
            instance.referenceImages.append(
                GoogleImagenRequest.Instance.ReferenceImage(
                    referenceType="REFERENCE_TYPE_RAW",
                    referenceId=0,
                    referenceImage=GoogleImagenRequest.Instance.ReferenceImage.Image(
                        bytesBase64Encoded=image_options.mask.data,
                    ),
                ),
            )
        parameters = GoogleImagenRequest.Parameters.from_image_options(image_options)

        return GoogleImagenRequest(instances=[instance], parameters=parameters), raw

    @abstractmethod
    def _request_url(self, model: Model) -> str:
        pass

    @abstractmethod
    async def _request_headers(self) -> dict[str, str]:
        pass

    @override
    async def _execute_request(self, request: GoogleImagenRequest, options: ProviderOptions) -> Response:
        data = request.model_dump(mode="json", exclude_none=True, by_alias=True)
        url = self._request_url(options.model)

        async with self._open_client(url) as client:
            response = await client.post(
                url,
                headers=await self._request_headers(),
                timeout=options.timeout,
                json=data,
            )
            response.raise_for_status()
            return response

    @override
    def _parse_response(
        self,
        response: Response,
        output_factory: Callable[[str, bool], StructuredOutput],
        raw_completion: RawCompletion,
        request: GoogleImagenRequest,
    ):
        try:
            raw = response.json()
        except JSONDecodeError:
            raw_completion.response = response.text
            res = self._unknown_error(response)
            res.set_response(response)
            raise res
        response_model = GoogleImagenResponse.model_validate(raw)
        return StructuredOutput(output={}, files=response_model.to_files())

    @override
    def _single_stream(
        self,
        request: GoogleImagenRequest,
        output_factory: Callable[[str, bool], StructuredOutput],
        partial_output_factory: Callable[[Any], StructuredOutput],
        raw_completion: RawCompletion,
        options: ProviderOptions,
    ) -> AsyncGenerator[StructuredOutput, None]:
        raise NotImplementedError("_single_stream is not supported for OpenAI Image")
