import asyncio
import base64
import copy
import logging
from collections.abc import Iterator
from io import BytesIO
from typing import Any, cast, override

import httpx
from pydantic import Field, ValidationError

from core.domain.consts import AUDIO_REF_NAME, FILE_DEFS, FILE_REF_NAME, IMAGE_REF_NAME, PDF_REF_NAME
from core.domain.errors import (
    BadRequestError,
    InvalidFileError,
    InvalidRunOptionsError,
    message_from_validation_error,
)
from core.domain.fields.file import File
from core.domain.models import Model, Provider
from core.domain.models.model_data import DeprecatedModel
from core.domain.models.model_datas_mapping import MODEL_DATAS
from core.domain.tool import Tool
from core.runners.workflowai.internal_tool import InternalTool
from core.tools import ToolKind
from core.utils.file_utils.file_utils import guess_content_type
from core.utils.schema_sanitation import get_file_format
from core.utils.schemas import JsonSchema
from core.utils.strings import clean_unicode_chars

_logger = logging.getLogger(__file__)


class FileWithKeyPath(File):
    key_path: list[str | int]
    storage_url: str | None = Field(default=None, description="The URL of the file in Azure Blob Storage")
    format: str | None = Field(default=None, description="The format of the file")

    @property
    def key_path_str(self) -> str:
        return ".".join(str(key) for key in self.key_path)

    @property
    @override
    def is_audio(self) -> bool | None:
        audio = super().is_audio
        if audio is not None:
            return audio
        if self.format is None:
            return None
        return self.format == "audio"

    @property
    @override
    def is_image(self) -> bool | None:
        image = super().is_image
        if image is not None:
            return image
        if self.format is None:
            return None
        return self.format == "image"


def _replace_file_in_payload(
    payload: dict[str, Any],
    key_path: list[str | int],
    format: str | None,
    append_to: list[FileWithKeyPath],
):
    try:
        valid = FileWithKeyPath.model_validate({**payload, "key_path": key_path, "format": format})
    except ValidationError as e:
        raise InvalidFileError(
            message_from_validation_error(e),
            file_url=payload.get("url"),
            details={"file": payload},
        ) from e
    payload.clear()
    payload["number"] = len(append_to)
    append_to.append(valid)


_ANNOYING_KEYS = ["allOf", "anyOf", "oneOf"]


def _handle_annoying_keys(
    schema: dict[str, Any],
    payload: Any,
    append_to: list[FileWithKeyPath],
    key_path: list[str | int],
    root_defs: dict[str, Any] | None,
) -> None:
    # Check for allOf, anyOf, oneOf and dives in as needed
    for key in _ANNOYING_KEYS:
        if key in schema:
            for sub_schema in schema[key]:
                _recursive_find_files(sub_schema, payload, append_to, key_path, root_defs)


def _process_list_payload(
    schema: dict[str, Any],
    payload: list[Any],
    append_to: list[FileWithKeyPath],
    key_path: list[str | int],
    root_defs: dict[str, Any] | None,
) -> None:
    # Process list payloads, handling 'items' and composite keys (anyOf, allOf, oneOf) to detect file references in arrays.
    if "items" in schema:
        for idx, item in enumerate(payload):
            _recursive_find_files(schema["items"], item, append_to, key_path + [idx], root_defs)
    for composite_key in _ANNOYING_KEYS:
        if composite_key in schema:
            for sub_schema in schema[composite_key]:
                _recursive_find_files(sub_schema, payload, append_to, key_path, root_defs)


def _process_ref(
    schema: dict[str, Any],
    payload: dict[str, Any],
    append_to: list[FileWithKeyPath],
    key_path: list[str | int],
    root_defs: dict[str, Any] | None,
) -> bool:
    ref_val: str = schema["$ref"]
    # Process '$ref' branches: If the ref is for File or Image, extract the file; otherwise, resolve the reference using root_defs.
    if ref_val.removeprefix("#/$defs/") in FILE_DEFS:
        _replace_file_in_payload(payload, key_path, get_file_format(ref_val, schema), append_to)
        return True

    if root_defs is not None and ref_val.startswith("#/$defs/"):
        def_name = ref_val.split("/")[-1]
        if def_name in root_defs:
            _recursive_find_files(root_defs[def_name], payload, append_to, key_path, root_defs)
            return True
    return False


def _recursive_find_files(
    schema: dict[str, Any],
    payload: Any,
    append_to: list[FileWithKeyPath],
    key_path: list[str | int],
    root_defs: dict[str, Any] | None,
) -> None:  # noqa: C901
    # Main recursive function to traverse the schema and payload and extract file references.
    # It delegates list payloads to _process_list_payload and '$ref' handling to _process_ref.
    if isinstance(payload, list):
        _process_list_payload(schema, cast(list[Any], payload), append_to, key_path, root_defs)
        return

    if not isinstance(payload, dict):
        return

    _handle_annoying_keys(schema, payload, append_to, key_path, root_defs)

    if "$ref" in schema:
        if _process_ref(schema, cast(dict[str, Any], payload), append_to, key_path, root_defs):
            return

    if "properties" in schema:
        for key, value in payload.items():  # type: ignore
            if key in schema["properties"]:
                _recursive_find_files(schema["properties"][key], value, append_to, key_path + [key], root_defs)


def is_schema_containing_file(schema: dict[str, Any]) -> bool:
    file_refs = {IMAGE_REF_NAME, FILE_REF_NAME, AUDIO_REF_NAME, PDF_REF_NAME}
    return "$defs" in schema and any(ref in schema["$defs"] for ref in file_refs)


def is_schema_containing_legacy_file(schema: dict[str, Any]) -> bool:
    return (
        "$defs" in schema
        and IMAGE_REF_NAME in schema["$defs"]
        and "url" not in schema["$defs"][IMAGE_REF_NAME].get("properties", {})
    )


def extract_files(schema: dict[str, Any], payload: Any) -> tuple[dict[str, Any], Any, list[FileWithKeyPath]]:
    """Navigate a payload and extracts images/files from it. Images are identified by the File/Image schema ref"""

    if not is_schema_containing_file(schema):
        return schema, payload, []

    out: list[FileWithKeyPath] = []
    payload = copy.deepcopy(payload)
    schema = copy.deepcopy(schema)
    root_defs: dict[str, Any] = schema.get("$defs", {})
    _recursive_find_files(schema, payload, out, [], root_defs)
    schema["$defs"]["File"] = {
        "type": "object",
        "properties": {
            "number": {"type": "integer", "description": "The index of the file message"},
        },
    }
    return schema, payload, out


def possible_file_keypaths(schema: dict[str, Any], file_count: int):
    """Recursively navigate the schema to find where to put the files. Returns a list of keypath of size file_count"""

    def _keypath_iterator(
        schema: JsonSchema,
        key_prefix: list[str | int],
        remaining_files: int,
    ) -> Iterator[list[str | int]]:
        for key, child in schema.child_iterator():
            if child.followed_ref_name in FILE_DEFS:
                # We found a file !
                # TODO: We should do some additional checks here, for example check
                # the expected file type but for now we only support images in output so we
                # can just fill the spots as they come in

                if isinstance(key, int):
                    # We are in a list ! so we can just fill all the spots
                    for idx in range(remaining_files):
                        yield [*key_prefix, idx]
                    # We have filled all the spots
                    return

                # Otherwise we have a single file so we can yield the keypath and continue
                yield [*key_prefix, key]
                # We have filled one spot
                remaining_files -= 1

                if remaining_files == 0:
                    # We have filled all the spots
                    return

            yield from _keypath_iterator(child, [*key_prefix, key], remaining_files)

    raw = JsonSchema(schema)
    return list(_keypath_iterator(raw, [], file_count))


_download_client = httpx.AsyncClient()


async def _fetch_file_with_retries(url: str, retries: int = 2) -> httpx.Response:
    try:
        return await _download_client.get(url)
    except (
        httpx.ConnectTimeout,
        httpx.ReadTimeout,
        httpx.ReadError,
        httpx.ConnectError,
        httpx.RemoteProtocolError,
    ) as e:
        if retries <= 0:
            raise InvalidFileError(
                f"Failed to download file: {e}",
                capture=False,
            )
        return await _fetch_file_with_retries(url, retries - 1)


async def download_file(file: File):
    if not file.url:
        raise InvalidFileError("File url is required when data is not provided")

    response = await _fetch_file_with_retries(file.url)

    if response.status_code != 200:
        raise InvalidFileError(
            f"Failed to file image: {response.status_code}",
            file_url=file.url,
            details={"response_status_code": response.status_code, "response_body": response.text},
        )

    file.data = base64.b64encode(response.content).decode("utf-8")

    if file.content_type is None:
        file.content_type = guess_content_type(response.content)
        if file.content_type is None:
            _logger.warning("Could not guess content type of url", extra={"url": file.url})

    return response.content


def sanitize_model_and_provider(model_str: str | None, provider_str: str | None) -> tuple[Model, Provider | None]:
    if not model_str:
        # We should never be here so we capture
        raise InvalidRunOptionsError("Model is required", capture=True)

    try:
        model = Model(model_str)
    except ValueError:
        raise InvalidRunOptionsError(f"Model {model_str} is not valid")

    data = MODEL_DATAS[model]  # noqa: F821
    if isinstance(data, DeprecatedModel):
        model = data.replacement_model

    try:
        provider = Provider(provider_str) if provider_str else None
    except ValueError:
        raise InvalidRunOptionsError(f"Provider {provider_str} is not valid")

    return model, provider


class ToolCallRecursionError(Exception):
    # Raised when all tool calls have already been called with the same arguments
    pass


def split_tools(
    available_tools: dict[ToolKind, InternalTool],
    tools: list[ToolKind | Tool] | None,
) -> tuple[dict[str, InternalTool], dict[str, Tool]]:
    internal_tools: dict[str, InternalTool] = {}
    external_tools: dict[str, Tool] = {}
    if not tools:
        return internal_tools, external_tools

    for tool in tools:
        if isinstance(tool, Tool):
            if tool.name.startswith("@"):
                raise BadRequestError(f"External tool name {tool.name} cannot start with @")
            external_tools[tool.name] = tool
            continue

        try:
            internal_tools[tool] = available_tools[tool]
        except (KeyError, ValueError):
            _logger.exception("Tool kind in enabled_tools is not available", extra={"tool": tool})
    return internal_tools, external_tools


async def convert_pdf_to_images(pdf_file: FileWithKeyPath) -> list[FileWithKeyPath]:
    # No need to wrap in a try-except block
    # The error will be caught upstream
    from pdf2image import convert_from_bytes  # pyright: ignore[reportUnknownVariableType]
    from PIL import Image

    if not pdf_file.data:
        pdf_data = await download_file(pdf_file)
    else:
        pdf_data = base64.b64decode(pdf_file.data)

    images = await asyncio.to_thread(convert_from_bytes, pdf_file=pdf_data, fmt="jpg", dpi=150)  # pyright: ignore[reportUnknownArgumentType]

    def _map(image: Image.Image, idx: int):
        # Convert PIL Image to bytes and encode as base64
        buffer = BytesIO()
        image.save(
            buffer,
            format="JPEG",
            quality=60,
            optimize=True,
            progressive=True,
        )
        image_bytes = buffer.getvalue()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        return FileWithKeyPath(data=image_base64, content_type="image/jpeg", key_path=pdf_file.key_path + [idx])

    return [_map(image, i) for i, image in enumerate(images)]


def cleanup_provider_json(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: cleanup_provider_json(v) for k, v in obj.items()}  # pyright: ignore[reportUnknownVariableType]
    if isinstance(obj, list):
        return [cleanup_provider_json(v) for v in obj]  # pyright: ignore[reportUnknownVariableType]
    if isinstance(obj, str):
        return clean_unicode_chars(obj)
    return obj
