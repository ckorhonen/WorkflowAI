from enum import Enum

from pydantic import BaseModel


class IntegrationPartner(str, Enum):
    INSTRUCTOR = "instructor"
    OPENAI_SDK = "openai-sdk"
    OPENAI_SDK_TS = "openai-sdk-ts"


class ProgrammingLanguage(str, Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"


class IntegrationKind(str, Enum):
    INSTRUCTOR_PYTHON = "instructor-python"
    OPENAI_SDK_PYTHON = "openai-sdk-python"
    OPENAI_SDK_TS = "openai-sdk-ts"


class Integration(BaseModel):
    integration_partner: IntegrationPartner
    programming_language: ProgrammingLanguage
    default_for_language: bool
    output_class: str
    display_name: str
    slug: IntegrationKind

    logo_url: str
    landing_page_snippet: str

    # Not all integration may support structured generation.
    landing_page_structured_generation_snippet: str | None = None

    integration_chat_initial_snippet: str
    integration_chat_agent_naming_snippet: str

    documentation_filepaths: list[str]
