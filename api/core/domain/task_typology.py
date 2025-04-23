from typing import Any, cast

from pydantic import BaseModel, Field

from core.domain.fields.file import FileKind
from core.utils.schema_sanitation import get_file_format
from core.utils.schemas import JsonSchema


class SchemaTypology(BaseModel):
    has_image: bool = Field(default=False, description="Whether the schema contains an image")
    has_audio: bool = Field(default=False, description="Whether the schema contains an audio")
    has_pdf: bool = Field(default=False, description="Whether the schema contains a pdf")

    def assign_from_schema(self, schema: JsonSchema, is_array: bool):
        followed: str | None = schema.get("$ref")
        if followed is None:
            is_array = schema.type == "array"
            for _, child in schema.child_iterator(follow_refs=False):
                self.assign_from_schema(child, is_array)
            return

        format = get_file_format(followed, cast(dict[str, Any], schema.schema))

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
        if input_schema.get("$defs"):
            raw.input.assign_from_schema(JsonSchema(schema=input_schema), False)

        if output_schema.get("$defs"):
            raw.output.assign_from_schema(JsonSchema(schema=output_schema), False)

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
