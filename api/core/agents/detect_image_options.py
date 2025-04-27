from typing import Any

import workflowai
from pydantic import BaseModel, Field

from core.domain.fields.image_options import ImageBackground, ImageFormat, ImageOptions, ImageQuality, ImageShape


class DetectImageOptionsInput(BaseModel):
    instructions: str
    input_schema: dict[str, Any]


class DetectImageOptionsOutput(BaseModel):
    class Options(BaseModel):
        quality: ImageQuality | None = None
        background: ImageBackground | None = None
        format: ImageFormat | None = None
        shape: ImageShape | None = None
        image_count: int | None = Field(
            default=None,
            description="A number of images to generate.",
        )

    image_options: Options | None = None

    def to_domain(self) -> ImageOptions | None:
        if not self.image_options:
            return None

        dumped = self.image_options.model_dump(exclude_none=True)
        return ImageOptions.model_validate(dumped)


@workflowai.agent(id="detect-image-options", model=workflowai.Model.GEMINI_2_0_FLASH_LITE_001)
async def detect_image_options(input: DetectImageOptionsInput) -> DetectImageOptionsOutput:
    """Extract default image options from the instructions. Only provide fields that are explicitly mentioned
    in the instructions. Do not fill fields that are already present in the input schema."""
    ...
