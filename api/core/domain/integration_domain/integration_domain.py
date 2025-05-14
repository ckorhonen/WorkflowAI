from enum import Enum

from pydantic import BaseModel

from core.domain.integration_domain.instruction_python_snippets import (
    INSTRUCTOR_PYTHON_INTEGRATION_CHAT_AGENT_NAMING_SNIPPET,
    INSTRUCTOR_PYTHON_INTEGRATION_CHAT_INITIAL_SNIPPET,
    INSTRUCTOR_PYTHON_LANDING_PAGE_SNIPPET,
    INSTRUCTOR_PYTHON_LANDING_PAGE_STRUCTURED_GENERATION_SNIPPET,
)
from core.domain.integration_domain.openai_sdk_python_snippets import (
    OPENAI_SDK_PYTHON_INTEGRATION_CHAT_AGENT_NAMING_SNIPPET,
    OPENAI_SDK_PYTHON_INTEGRATION_CHAT_INITIAL_SNIPPET,
    OPENAI_SDK_PYTHON_LANDING_PAGE_SNIPPET,
    OPENAI_SDK_PYTHON_LANDING_PAGE_STRUCTURED_GENERATION_SNIPPET,
)
from core.domain.integration_domain.openai_sdk_ts_snippets import (
    OPENAI_SDK_TS_INTEGRATION_CHAT_AGENT_NAMING_SNIPPET,
    OPENAI_SDK_TS_INTEGRATION_CHAT_INITIAL_SNIPPET,
    OPENAI_SDK_TS_LANDING_PAGE_SNIPPET,
    OPENAI_SDK_TS_LANDING_PAGE_STRUCTURED_GENERATION_SNIPPET,
)

WORKFLOWAI_API_KEY_PLACEHOLDER = "<WORKFLOWAI_API_KEY_PLACEHOLDER>"
PROPOSED_AGENT_NAME_AND_MODEL_PLACEHOLDER = "<PROPOSED_AGENT_NAME_PLACEHOLDER>"


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


OFFICIAL_INTEGRATIONS = [
    Integration(
        integration_partner=IntegrationPartner.INSTRUCTOR,
        programming_language=ProgrammingLanguage.PYTHON,
        default_for_language=False,
        output_class="pydantic.BaseModel",
        display_name="Instructor (Python)",
        slug=IntegrationKind.INSTRUCTOR_PYTHON,
        logo_url="https://workflowai.blob.core.windows.net/workflowai-public/python.png",
        landing_page_snippet=INSTRUCTOR_PYTHON_LANDING_PAGE_SNIPPET,
        landing_page_structured_generation_snippet=INSTRUCTOR_PYTHON_LANDING_PAGE_STRUCTURED_GENERATION_SNIPPET,
        integration_chat_initial_snippet=INSTRUCTOR_PYTHON_INTEGRATION_CHAT_INITIAL_SNIPPET,
        integration_chat_agent_naming_snippet=INSTRUCTOR_PYTHON_INTEGRATION_CHAT_AGENT_NAMING_SNIPPET,
        documentation_filepaths=[
            "developers/python/instructor.md",
        ],
    ),
    Integration(
        integration_partner=IntegrationPartner.OPENAI_SDK,
        programming_language=ProgrammingLanguage.PYTHON,
        default_for_language=True,
        output_class="pydantic.BaseModel",
        display_name="OpenAI SDK (Python)",
        slug=IntegrationKind.OPENAI_SDK_PYTHON,
        logo_url="https://workflowai.blob.core.windows.net/workflowai-public/python.png",
        landing_page_snippet=OPENAI_SDK_PYTHON_LANDING_PAGE_SNIPPET,
        landing_page_structured_generation_snippet=OPENAI_SDK_PYTHON_LANDING_PAGE_STRUCTURED_GENERATION_SNIPPET,
        integration_chat_initial_snippet=OPENAI_SDK_PYTHON_INTEGRATION_CHAT_INITIAL_SNIPPET,
        integration_chat_agent_naming_snippet=OPENAI_SDK_PYTHON_INTEGRATION_CHAT_AGENT_NAMING_SNIPPET,
        documentation_filepaths=[
            "developers/python/openai.md",
        ],
    ),
    Integration(
        integration_partner=IntegrationPartner.OPENAI_SDK,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        default_for_language=True,
        output_class="zod.z.object",
        display_name="OpenAI SDK (TypeScript)",
        slug=IntegrationKind.OPENAI_SDK_TS,
        logo_url="https://workflowai.blob.core.windows.net/workflowai-public/typescript.png",
        landing_page_snippet=OPENAI_SDK_TS_LANDING_PAGE_SNIPPET,
        landing_page_structured_generation_snippet=OPENAI_SDK_TS_LANDING_PAGE_STRUCTURED_GENERATION_SNIPPET,
        integration_chat_initial_snippet=OPENAI_SDK_TS_INTEGRATION_CHAT_INITIAL_SNIPPET,
        integration_chat_agent_naming_snippet=OPENAI_SDK_TS_INTEGRATION_CHAT_AGENT_NAMING_SNIPPET,
        documentation_filepaths=[
            "developers/js/openai.md",
        ],
    ),
]


def default_integration_for_language(language: ProgrammingLanguage) -> Integration:
    for integration in OFFICIAL_INTEGRATIONS:
        if integration.programming_language == language and integration.default_for_language:
            return integration
    raise ValueError(f"No default integration found for language: {language}")
