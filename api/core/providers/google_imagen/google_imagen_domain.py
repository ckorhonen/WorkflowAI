from typing import Literal

from pydantic import BaseModel

from core.domain.fields.file import File
from core.domain.fields.image_options import ImageOptions, ImageShape


# Ref https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/imagen-api?authuser=2
class GoogleImagenRequest(BaseModel):
    class Instance(BaseModel):
        prompt: str

        class ReferenceImage(BaseModel):
            referenceType: Literal["REFERENCE_TYPE_MASK", "REFERENCE_TYPE_RAW"]
            referenceId: int

            class Image(BaseModel):
                bytesBase64Encoded: str

            referenceImage: Image

        referenceImages: list[ReferenceImage] | None = None

    instances: list[Instance]

    class Parameters(BaseModel):
        sampleCount: int = 1
        aspectRatio: Literal["1:1", "9:16", "16:9", "4:3", "3:4"] | None = None
        personGeneration: Literal["allow_adult", "dont_allow", "allow_all"] | None = None
        safetySetting: (
            Literal["block_low_and_above", "block_medium_and_above", "block_only_high", "block_none"] | None
        ) = None

        @classmethod
        def _map_shape(cls, shape: ImageShape):
            match shape:
                case "square":
                    return "1:1"
                case "portrait":
                    return "9:16"
                case "landscape":
                    return "16:9"

        @classmethod
        def from_image_options(cls, image_options: ImageOptions):
            return cls(
                sampleCount=image_options.image_count or 1,
                aspectRatio=cls._map_shape(image_options.shape),
            )

    parameters: Parameters | None = None


class GoogleImagenResponse(BaseModel):
    class Image(BaseModel):
        mimeType: str
        bytesBase64Encoded: str

    predictions: list[Image] | None = None

    def to_files(self) -> list[File]:
        if not self.predictions:
            return []
        return [File(data=image.bytesBase64Encoded, content_type=image.mimeType) for image in self.predictions]
