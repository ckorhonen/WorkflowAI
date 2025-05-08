import hashlib
import json
import re
from typing import Any, Literal, Self

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from core.domain.errors import UnpriceableRunError
from core.domain.fields.file import File
from core.domain.llm_usage import LLMUsage
from core.domain.message import MessageDeprecated
from core.domain.models import Model
from core.domain.task_group_properties import ToolChoice, ToolChoiceFunction
from core.providers.base.models import (
    AudioContentDict,
    DocumentContentDict,
    ImageContentDict,
    StandardMessage,
    TextContentDict,
    ToolCallRequestDict,
    ToolCallResultDict,
)
from core.providers.google.google_provider_domain import (
    internal_tool_name_to_native_tool_call,
    native_tool_name_to_internal,
)
from core.utils.json_utils import safe_extract_dict_from_json
from core.utils.token_utils import tokens_from_string


class ResponseFormat(BaseModel):
    type: Literal["json_object", "text"] = "json_object"


class FunctionParameters(BaseModel):
    name: str
    description: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)


class Tool(BaseModel):
    type: Literal["function"]
    function: FunctionParameters


class TextChunk(BaseModel):
    type: Literal["text"] = "text"
    text: str

    def to_standard(self) -> TextContentDict:
        return {"type": "text", "text": self.text}


class ImageURL(BaseModel):
    url: str


class ImageURLChunk(BaseModel):
    type: Literal["image_url"] = "image_url"
    image_url: ImageURL

    def to_standard(self) -> ImageContentDict:
        return {"type": "image_url", "image_url": {"url": self.image_url.url}}

    @classmethod
    def from_file(cls, file: File) -> Self:
        return cls(image_url=ImageURL(url=file.to_url(default_content_type="image/*")))


class DocumentURLChunk(BaseModel):
    type: Literal["document_url"] = "document_url"
    document_url: str

    def to_standard(self) -> DocumentContentDict:
        return {"type": "document_url", "source": {"url": self.document_url}}


_role_to_map: dict[MessageDeprecated.Role, Literal["user", "assistant", "system"]] = {
    MessageDeprecated.Role.SYSTEM: "system",
    MessageDeprecated.Role.USER: "user",
    MessageDeprecated.Role.ASSISTANT: "assistant",
}


class ToolCallFunction(BaseModel):
    name: str
    arguments: dict[str, Any] | str


class ToolCall(BaseModel):
    id: str | None = None
    type: Literal["function"] = "function"
    function: ToolCallFunction
    index: int | None = None

    @field_validator("id")
    def validate_id(cls, v: str | None) -> str | None:
        """Sanitize the tool call id to be a valid Mistral tool call id.
        "must be a-z, A-Z, 0-9, with a length of 9." from the mistral error message
        """
        if not v:
            return None
        if re.match(r"^[a-zA-Z0-9_-]{9}", v) is not None:
            return v
        # Otherwise we hash the tool call id as a hex and take the first 9 characters
        return hashlib.sha256(v.encode()).hexdigest()[:9]


class MistralAIMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str | list[TextChunk | ImageURLChunk | DocumentURLChunk]
    tool_calls: list[ToolCall] | None = None

    @classmethod
    def from_domain(cls, message: MessageDeprecated):
        # Since Mistral domain has not been converted to use native tools in messages yet.

        role = _role_to_map[message.role]
        if not message.files:
            content: str | list[TextChunk | ImageURLChunk | DocumentURLChunk] = message.content
        else:
            content: str | list[TextChunk | ImageURLChunk | DocumentURLChunk] = []
            if message.content:
                content.append(TextChunk(text=message.content))
            for file in message.files or []:
                if file.is_image:
                    content.append(ImageURLChunk.from_file(file))
                else:
                    content.append(DocumentURLChunk(document_url=file.to_url(default_content_type="application/pdf")))

        tool_calls: list[ToolCall] = []
        if message.tool_call_requests:
            tool_calls.extend(
                [
                    ToolCall(
                        id=tool.id,
                        function=ToolCallFunction(
                            name=internal_tool_name_to_native_tool_call(tool.tool_name),
                            arguments=tool.tool_input_dict,
                        ),
                    )
                    for tool in message.tool_call_requests
                ],
            )

        return cls(content=content, role=role, tool_calls=tool_calls if tool_calls else None)

    def to_standard(self) -> StandardMessage:
        content: (
            str
            | list[
                TextContentDict
                | ImageContentDict
                | AudioContentDict
                | DocumentContentDict
                | ToolCallRequestDict
                | ToolCallResultDict
            ]
        ) = []
        if isinstance(self.content, str):
            if not self.tool_calls:
                return {"role": self.role, "content": self.content}
            content.append(TextContentDict(type="text", text=self.content))
        else:
            content.extend([item.to_standard() for item in self.content])

        if self.tool_calls:
            content.extend(
                [
                    ToolCallRequestDict(
                        type="tool_call_request",
                        id=item.id,
                        tool_name=native_tool_name_to_internal(item.function.name),
                        tool_input_dict=safe_extract_dict_from_json(item.function.arguments),
                    )
                    for item in self.tool_calls
                ],
            )
        return {"role": self.role, "content": content}

    def token_count(self, model: Model) -> int:
        token_count = 0

        if isinstance(self.content, str):
            return tokens_from_string(self.content, model)

        for block in self.content:
            if isinstance(block, TextChunk):
                token_count += tokens_from_string(block.text, model)
            else:
                raise UnpriceableRunError("Token counting for files is not implemented")

        return token_count


MistralToolChoiceEnum = Literal["auto", "none", "required", "any"]


class MistralToolChoice(BaseModel):
    type: Literal["function"] = "function"

    class FunctionName(BaseModel):
        name: str

    function: FunctionName


class MistralToolMessage(BaseModel):
    role: Literal["tool"]
    tool_call_id: str
    name: str
    content: str

    @classmethod
    def from_domain(cls, message: MessageDeprecated) -> list[Self]:
        ret: list[Self] = []
        for tool in message.tool_call_results or []:
            result = safe_extract_dict_from_json(tool.result)
            if not result:
                result = {"result": tool.result}
            ret.append(
                cls(
                    role="tool",
                    tool_call_id=tool.id,
                    name=internal_tool_name_to_native_tool_call(tool.tool_name),
                    content=json.dumps(result),
                ),
            )
        return ret

    @classmethod
    def to_standard(cls, messages: list[Self]) -> StandardMessage:
        contents: list[
            TextContentDict
            | ImageContentDict
            | AudioContentDict
            | DocumentContentDict
            | ToolCallRequestDict
            | ToolCallResultDict
        ] = []

        contents.extend(
            [
                ToolCallResultDict(
                    type="tool_call_result",
                    id=message.tool_call_id,
                    tool_name=message.name,
                    tool_input_dict=None,
                    result=message.content,
                    error=None,
                )
                for message in messages
            ],
        )

        return StandardMessage(
            role="user",
            content=contents,
        )

    def token_count(self, model: Model) -> int:
        # Very basic implementation of the pricing of tool calls messages.
        # We'll need to double check the pricing rules for every provider
        # When working on https://linear.app/workflowai/issue/WOR-3730
        return tokens_from_string(self.content, model)


class CompletionRequest(BaseModel):
    model: str
    temperature: float = 0.3
    top_p: float | None = None
    max_tokens: int | None = None
    stream: bool = False
    stop: str | None = None
    random_seed: int | None = None
    messages: list[MistralAIMessage | MistralToolMessage]
    response_format: ResponseFormat = Field(default_factory=ResponseFormat)
    tools: list[Tool] | None = None
    tool_choice: MistralToolChoiceEnum | MistralToolChoice | None = None
    safe_prompt: bool | None = None

    @classmethod
    def tool_choice_from_domain(
        cls,
        tool_choice: ToolChoice | None,
    ) -> MistralToolChoiceEnum | MistralToolChoice | None:
        if not tool_choice:
            return None
        if isinstance(tool_choice, ToolChoiceFunction):
            return MistralToolChoice(type="function", function=MistralToolChoice.FunctionName(name=tool_choice.name))
        return tool_choice


class AssistantMessage(BaseModel):
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    # prefix: bool = False
    # role: Literal["assistant"] = "assistant"


FinishReasonEnum = Literal["stop", "length", "model_length", "error", "tool_calls"]


class ChatCompletionChoice(BaseModel):
    # index: int
    message: AssistantMessage
    finish_reason: str | FinishReasonEnum | None = None


class Usage(BaseModel):
    # Values are supposedly not optional, just adding None to be safe
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None

    def to_domain(self):
        return LLMUsage(
            prompt_token_count=self.prompt_tokens,
            completion_token_count=self.completion_tokens,
        )


class CompletionResponse(BaseModel):
    # Since we validate the response, not adding fields we do not use
    # id: str
    # object: str
    # model: str
    usage: Usage
    created: int
    choices: list[ChatCompletionChoice]


class MistralError(BaseModel):
    # loc: list[str | int] | None = None
    message: str | None = Field(default=None, validation_alias=AliasChoices("message", "msg"))
    type: str | None = None
    # param: str | None = None
    # code: str | None = None

    class _Detail(BaseModel):
        type: str | None = None
        msg: str | None = None

    # Sometimes we get a list of details instead of having the
    # message and type at the root
    detail: list[_Detail] | None = None

    model_config = ConfigDict(extra="allow")

    @property
    def actual_type(self) -> str | None:
        if self.detail:
            return self.detail[0].type
        return self.type

    @property
    def actual_message(self) -> str | None:
        if self.detail:
            return self.detail[0].msg
        return self.message


class DeltaMessage(BaseModel):
    role: str | None = None
    content: str | None = None
    tool_calls: list[ToolCall] | None = None


class CompletionResponseStreamChoice(BaseModel):
    # index: int
    delta: DeltaMessage | None = None
    finish_reason: FinishReasonEnum | str | None = None


class CompletionChunk(BaseModel):
    # id: str
    # object: str
    # created: int
    # model: str
    usage: Usage | None = None
    choices: list[CompletionResponseStreamChoice] | None = None
