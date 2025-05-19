from pydantic import BaseModel, Field


class ModelDataSupports(BaseModel):
    supports_json_mode: bool = Field(description="Whether the model supports JSON mode")
    supports_input_image: bool = Field(description="Whether the model supports input images")
    supports_input_pdf: bool = Field(description="Whether the model supports input pdfs")
    supports_input_audio: bool = Field(description="Whether the model supports input audio")
    supports_audio_only: bool = Field(
        default=False,
        description="Whether the model supports audio only",
    )
    support_system_messages: bool = Field(default=True, description="Whether the model supports system messages")
    supports_structured_output: bool = Field(default=False, description="Whether the model supports structured output")
    support_input_schema: bool = Field(default=True, description="Whether the model supports input schema")
    supports_output_image: bool = Field(default=False, description="Whether the model supports output images")
    supports_output_text: bool = Field(default=True, description="Whether the model supports output text")
    supports_parallel_tool_calls: bool = Field(
        default=True,
        description="Whether the model supports parallel tool calls",
    )
