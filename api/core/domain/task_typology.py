from typing import Any, cast

from pydantic import BaseModel, Field

from core.domain.consts import FILE_DEFS
from core.domain.fields.file import FileKind
from core.utils.schema_sanitation import get_file_format
from core.utils.schemas import JsonSchema


class SchemaTypology(BaseModel):
    has_text: bool = Field(default=False, description="Whether the schema contains text")
    has_image: bool = Field(default=False, description="Whether the schema contains an image")
    has_audio: bool = Field(default=False, description="Whether the schema contains an audio")
    has_pdf: bool = Field(default=False, description="Whether the schema contains a pdf")

    @property
    def is_text_only(self) -> bool:
        return not self.has_image and not self.has_audio and not self.has_pdf

    def assign_from_schema(self, schema: JsonSchema):
        if "$defs" not in schema.schema:
            # Shortcut for when we don't have any defs
            # It must have text since it has nothing else
            self.has_text = True
            return

        for _, field_type, child in schema.fields_iterator([], dive=lambda r: r.followed_ref_name not in FILE_DEFS):
            if field_type != "object" and field_type != "array":
                self.has_text = True
                continue

            followed: str | None = child.followed_ref_name
            if followed is None:
                continue

            format = get_file_format(followed, cast(dict[str, Any], child.schema))

            match format:
                case FileKind.IMAGE:
                    self.has_image = True
                case FileKind.AUDIO:
                    self.has_audio = True
                case FileKind.PDF:
                    self.has_pdf = True
                case _:
                    pass


class TaskTypology(BaseModel):
    input: SchemaTypology = Field(default_factory=SchemaTypology)
    output: SchemaTypology = Field(default_factory=SchemaTypology)

    @classmethod
    def from_schema(cls, input_schema: dict[str, Any], output_schema: dict[str, Any]):
        raw = TaskTypology()
        # No defs, so typology is empty

        raw.input.assign_from_schema(JsonSchema(schema=input_schema))
        raw.output.assign_from_schema(JsonSchema(schema=output_schema))

        return raw

    def __str__(self):
        typology_desc: list[str] = []
        if self.output.has_image:
            typology_desc.append("image output")
        if self.input.has_image:
            typology_desc.append("image input")
        if self.input.has_audio:
            typology_desc.append("audio input")
        if not typology_desc:
            typology_desc.append("text only")
        return " + ".join(typology_desc)
