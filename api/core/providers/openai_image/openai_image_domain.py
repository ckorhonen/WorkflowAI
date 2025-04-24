from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from core.domain.fields.file import File


class OpenAIImageRequest(BaseModel):
    prompt: str = Field(description="A text description of the desired image(s).")
    model: str = Field(default="dall-e-2", description="The model to use for image generation.")
    n: int = Field(default=1, ge=1, le=10, description="The number of images to generate.")
    quality: Literal["high", "medium", "low", "auto"] = Field(
        default="auto",
        description="The quality of the image that will be generated.",
    )
    moderation: Literal["auto", "low"] = Field(
        default="auto",
        description="The moderation level of the generated images.",
    )
    size: Literal["1024x1024", "1792x1024", "1024x1792"] = Field(
        default="1024x1024",
        description="The size of the generated images.",
    )
    style: Literal["vivid", "natural"] = Field(default="vivid", description="The style of the generated images.")
    output_format: Literal["png", "jpeg", "webp"] = Field(
        default="png",
        description="The format of the generated images.",
    )
    background: Literal["transparent", "opaque", "auto"] = Field(
        default="auto",
        description="The background color of the generated images.",
    )

    image: str | list[str] | None = Field(description="The image to edit.")
    mask: str | list[str] | None = Field(description="The mask to use for the image.")

    @property
    def is_edit_request(self) -> bool:
        return self.image is not None or self.mask is not None

    @property
    def content_type(self) -> str:
        match self.output_format:
            case "png":
                return "image/png"
            case "jpeg":
                return "image/jpeg"
            case "webp":
                return "image/webp"


class OpenAIImageResponse(BaseModel):
    created: int = Field(description="The Unix timestamp of when the image was created.")

    class Data(BaseModel):
        url: Optional[str] = Field(default=None, description="The URL of the generated image.")
        b64_json: Optional[str] = Field(default=None, description="The base64-encoded JSON of the generated image.")

        def to_file(self, content_type: str) -> File:
            return File(data=self.b64_json, content_type=content_type)

    data: List[Data] = Field(description="The list of generated images.")

    class Usage(BaseModel):
        total_tokens: int = Field(description="The total number of tokens used in the request.")
        input_tokens: int = Field(description="The number of tokens used in the prompt.")
        output_tokens: int = Field(description="The number of tokens used in the completion.")

        class InputTokenDetails(BaseModel):
            text_tokens: int = Field(description="The number of text tokens used in the prompt.")
            image_tokens: int = Field(description="The number of image tokens used in the prompt.")

        input_token_details: InputTokenDetails = Field(
            ...,
            description="The details of the input tokens used in the request.",
        )
