from typing import Literal, Optional

from pydantic import BaseModel, Field

from core.domain.fields.file import File
from core.domain.fields.image_options import ImageBackground, ImageFormat, ImageOptions, ImageQuality, ImageShape
from core.domain.llm_usage import LLMUsage
from core.domain.models.models import Model


class OpenAIImageRequest(BaseModel):
    prompt: str = Field(description="A text description of the desired image(s).")
    model: str = Field(description="The model to use for image generation.")
    n: int = Field(default=1, ge=1, le=10, description="The number of images to generate.")
    quality: Literal["high", "medium", "low", "auto"] = Field(
        default="auto",
        description="The quality of the image that will be generated.",
    )
    # TODO: unused for now
    # moderation: Literal["auto", "low"] | None = Field(
    #     default="auto",
    #     description="The moderation level of the generated images.",
    # )
    size: Literal["1024x1024", "1536x1024", "1024x1536"] = Field(
        default="1024x1024",
        description="The size of the generated images.",
    )
    output_format: Literal["png", "jpeg", "webp"] = Field(
        default="png",
        description="The format of the generated images.",
    )
    background: Literal["transparent", "opaque", "auto"] | None = Field(
        default=None,
        description="The background color of the generated images.",
    )

    images: list[File] | None = None
    mask: File | None = None

    @property
    def content_type(self) -> str:
        match self.output_format:
            case "png":
                return "image/png"
            case "jpeg":
                return "image/jpeg"
            case "webp":
                return "image/webp"

    @classmethod
    def _map_format(cls, format: ImageFormat) -> Literal["png", "jpeg", "webp"]:
        return format

    @classmethod
    def _map_shape(cls, shape: ImageShape) -> Literal["1024x1024", "1536x1024", "1024x1536"]:
        match shape:
            case "square":
                return "1024x1024"
            case "portrait":
                return "1024x1536"
            case "landscape":
                return "1536x1024"

    @classmethod
    def _map_background(cls, background: ImageBackground) -> Literal["transparent", "opaque", "auto"]:
        return background

    @classmethod
    def _map_quality(cls, quality: ImageQuality) -> Literal["low", "medium", "high"]:
        return quality

    @classmethod
    def build(cls, prompt: str, image_options: ImageOptions, model: Model):
        return OpenAIImageRequest(
            prompt=prompt,
            n=image_options.image_count or 1,
            model=model,
            quality=cls._map_quality(image_options.quality),
            background=cls._map_background(image_options.background),
            output_format=cls._map_format(image_options.format),
            size=cls._map_shape(image_options.shape),
        )


class OpenAIImageResponse(BaseModel):
    class Data(BaseModel):
        url: Optional[str] = Field(default=None, description="The URL of the generated image.")
        b64_json: Optional[str] = Field(default=None, description="The base64-encoded JSON of the generated image.")

        def to_file(self, content_type: str) -> File:
            return File(data=self.b64_json, content_type=content_type)

    data: list[Data] = Field(description="The list of generated images.")

    class Usage(BaseModel):
        total_tokens: int | None = Field(default=None, description="The total number of tokens used in the request.")
        input_tokens: int | None = Field(default=None, description="The number of tokens used in the prompt.")
        output_tokens: int | None = Field(default=None, description="The number of tokens used in the completion.")

        class InputTokenDetails(BaseModel):
            text_tokens: int | None = Field(default=None, description="The number of text tokens used in the prompt.")
            image_tokens: int | None = Field(default=None, description="The number of image tokens used in the prompt.")

        input_token_details: InputTokenDetails | None = Field(
            default=None,
            description="The details of the input tokens used in the request.",
        )

        def assign(self, usage: LLMUsage):
            if self.input_token_details:
                usage.prompt_token_count = self.input_token_details.text_tokens
                usage.prompt_image_token_count = self.input_token_details.image_tokens
            usage.completion_image_token_count = self.output_tokens

    usage: Usage | None = Field(default=None, description="The usage details of the request.")
