import workflowai
from pydantic import BaseModel, Field
from workflowai import Model

from core.domain.fields.chat_message import ChatMessage


class DetectCompanyDomainTaskInput(BaseModel):
    messages: list[ChatMessage] = Field(
        description="The list of messages between the user and the assistant. The last message is the most recent one.",
    )


class DetectCompanyDomainTaskOutput(BaseModel):
    company_domain: str | None = Field(
        default=None,
        description="The detected company domain, if any. If several company domains are detected, return the latest one.",
    )
    failure_assistant_answer: str | None = Field(
        default=None,
        description="The assistant answer, in case a valid company domain is not provided, used to ask the user for a valid company domain",
    )


@workflowai.agent(id="detect-company-domain", model=Model.GEMINI_2_0_FLASH_LATEST)
async def run_detect_company_domain_task(input: DetectCompanyDomainTaskInput) -> DetectCompanyDomainTaskOutput:
    """You are a domain detection specialist tasked with identifying company domains from conversations.

    Analyze the messages to detect any company domain mentioned (e.g., 'company.com').

    In case the user passes a personal email address (ex: @gmail.com, @outlook.com, @icloud.com); kindly explain that our product requires a company email to work. google.com, microsoft.com and apple.com are valid work email.
    If a domain is found, return it in the 'company_domain' field.

    If multiple domains are mentioned, return the most recently mentioned one.

    If no domain is detected, provide a polite response in the failure_assistant_answer field asking the user to specify the company domain."""
    ...
