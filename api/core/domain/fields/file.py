import mimetypes
import re
from base64 import b64decode
from enum import StrEnum
from typing import Any, Self
from urllib.parse import parse_qs, urlparse

from pydantic import BaseModel, ConfigDict, Field, ModelWrapValidatorHandler, model_validator
from pydantic.json_schema import SkipJsonSchema

from core.domain.errors import InternalError
from core.utils.file_utils.file_utils import guess_content_type


class FileKind(StrEnum):
    DOCUMENT = "document"  # includes text, pdfs and images
    IMAGE = "image"
    AUDIO = "audio"
    PDF = "pdf"
    ANY = "any"

    def to_ref_name(self) -> str:
        match self:
            case FileKind.IMAGE:
                return "Image"
            case FileKind.AUDIO:
                return "Audio"
            case FileKind.DOCUMENT:
                return "File"
            case FileKind.PDF:
                return "PDF"
            case FileKind.ANY:
                return "File"

    @classmethod
    def from_ref_name(cls, ref_name: str):
        match ref_name:
            case "Image":
                return cls.IMAGE
            case "Audio":
                return cls.AUDIO
            case "PDF":
                return cls.PDF
            case _:
                return None


def _remove_additional_properties_from_json_schema(model: dict[str, Any]):
    model.pop("additionalProperties", None)


class File(BaseModel):
    content_type: str | None = Field(
        default=None,
        description="The content type of the file",
        examples=["image/png", "image/jpeg", "audio/wav", "application/pdf"],
    )
    data: str | None = Field(default=None, description="The base64 encoded data of the file")
    url: str | None = Field(default=None, description="The URL of the image")

    format: SkipJsonSchema[FileKind | str | None] = Field(
        default=None,
    )

    # We allow extra properties so that we don't lose values when validating jsons
    # from FileWithKeyPath for example
    model_config = ConfigDict(extra="allow", json_schema_extra=_remove_additional_properties_from_json_schema)

    def to_url(self, default_content_type: str | None = None) -> str:
        if self.data and (self.content_type or default_content_type):
            return f"data:{self.content_type or default_content_type};base64,{self.data}"
        if self.url:
            return self.url

        raise InternalError("No data or URL provided for image")

    @classmethod
    def _validate_base64(cls, data: str) -> bytes:
        # TODO: maybe we do not need to decode the data here, just check the padding
        # That's a lot of memory usage for no reason
        try:
            return b64decode(data)
        except Exception:
            raise ValueError("Invalid base64 data in file")

    def _validate_url_and_set_content_type(self, url: str):
        if url.startswith("data:"):
            content_type, data = _parse_data_url(url[5:])
            self.content_type = content_type
            self._validate_base64(data)
            self.data = data
            self.url = None
            return

        try:
            parsed = urlparse(url)
        except Exception as e:
            raise ValueError(f"Invalid URL provided for file: {e}")
        # TODO: add this check, right now it fails a lot of tests
        # if not parsed.scheme:
        #     raise ValueError("URL must have a scheme")

        if self.content_type:
            return

        if parsed.query:
            query_params = parse_qs(parsed.query)
            if "content_type" in query_params:
                self.content_type = query_params["content_type"][0]
                return

        if mime_type := mimetypes.guess_type(url, strict=False)[0]:
            self.content_type = mime_type

    @model_validator(mode="wrap")
    @classmethod
    def wrap_validator(cls, data: Any, handler: ModelWrapValidatorHandler[Self]) -> Self:
        if isinstance(data, str):
            data = {"url": data}

        validated = handler(data)

        if validated.data:
            decoded_data = cls._validate_base64(validated.data)
            if not validated.content_type:
                validated.content_type = guess_content_type(decoded_data)
            return validated
        if validated.url:
            validated._validate_url_and_set_content_type(validated.url)
            return validated

        raise ValueError("No data or URL provided for image")

    @property
    def is_image(self) -> bool | None:
        if self.content_type:
            return self.content_type.startswith("image/")
        if self.format is None:
            return None
        return self.format == "image"

    @property
    def is_audio(self) -> bool | None:
        if self.content_type:
            return self.content_type.startswith("audio/")
        if self.format is None:
            return None
        return self.format == "audio"

    @property
    def is_video(self) -> bool | None:
        if not self.content_type:
            return None
        return self.content_type.startswith("video/")

    @property
    def is_pdf(self) -> bool | None:
        if self.content_type:
            return self.content_type == "application/pdf"
        if self.format is None:
            return None
        return self.format == "pdf"

    @property
    def is_text(self) -> bool | None:
        if not self.content_type:
            return None
        return self.content_type in ["text/plain", "text/markdown", "text/csv", "text/json", "text/html"]

    def get_extension(self) -> str:
        if self.content_type:
            return mimetypes.guess_extension(self.content_type) or ""
        return ""

    def content_bytes(self) -> bytes | None:
        if self.data:
            return b64decode(self.data)
        return None

    def template_key(self) -> str | None:
        """Returns the key path for a value if the url of the file is templated"""
        if self.url and (match := _template_var_regexp.match(self.url)):
            return match.group(1).strip()
        return None


_template_var_regexp = re.compile(r"\{\{([^}]+)\}\}")


def _parse_data_url(data_url: str) -> tuple[str, str]:
    splits = data_url.split(";base64,")
    if len(splits) != 2:
        raise ValueError("Invalid base64 data URL")
    return splits[0], splits[1]


class FileWithKeyPath(File):
    """An extension of a File that contains a key path and a storage URL"""

    key_path: list[str | int]
    storage_url: str | None = Field(default=None, description="The URL of the file in Azure Blob Storage")

    @property
    def key_path_str(self) -> str:
        return ".".join(str(key) for key in self.key_path)
