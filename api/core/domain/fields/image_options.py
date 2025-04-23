from typing import Literal

from pydantic import BaseModel

from core.domain.fields.file import File


class ImageOptions(BaseModel):
    """An extra field to specify image parameters"""

    quality: Literal["low", "medium", "high"]
    mask: File | None = None
    background: Literal["opaque", "transparent", "auto"] = "auto"
    format: Literal["png", "jpeg", "webp"] = "png"
    shape: Literal["square", "portrait", "landscape"] = "square"
