import logging
from typing import Optional

import workflowai
from pydantic import BaseModel
from workflowai import Model

from core.utils.email_utils import safe_domain_from_email

from .company_domain_from_email_agent import (
    ClassifyEmailDomainAgentInput,
    ClassifyEmailDomainAgentOutput,
    run_classify_email_domain_agent,
)

_logger = logging.getLogger(__name__)


class ExtractCompanyInfoFromDomainTaskInput(BaseModel):
    company_domain: Optional[str] = None


class Product(BaseModel):
    name: str | None = None
    features: list[str] | None = None
    description: str | None = None
    target_users: list[str] | None = None


class ExtractCompanyInfoFromDomainTaskOutput(BaseModel):
    source_urls: list[str] | None = None
    company_name: str | None = None
    description: str | None = None
    locations: list[str] | None = None
    industries: list[str] | None = None
    products: list[Product] | None = None


@workflowai.agent(id="extract-company-info-from-domain", model=Model.GEMINI_2_0_FLASH_LATEST)
async def _extract_company_info_from_domain(
    input: ExtractCompanyInfoFromDomainTaskInput,
) -> ExtractCompanyInfoFromDomainTaskOutput:
    """You are a KYC expert specializing in gathering information about client companies.

    - Always use the @browser-text tool to browse the company's website using the provided 'company_domain'. Extract relevant information about:
    - company name
    - description
    - locations
    - industries
    - main products or services, including their target users.

    - If needed, use the @search tool to quickly find relevant URLs. For example, use 'site:<company_domain> <your query>'.

    - Compile the gathered information into the output format:
    - source_urls: List the URLs of the sources used to gather the information.
    - company_name: Provide the full name of the company.
    - description: Write a brief, synthesized description of the company's main activities or purpose based on multiple sources.
    - locations: List the company's locations, which may include headquarters, major offices, or countries of operation.
    - industries: List the industries or sectors in which the company operates. Be specific and accurate in naming the industries based on the information found.
    - products: Provide a list of the company's main products or services. For each product or service, include:
    - name: The name of the product or service
    - features: A list of key features or characteristics
    - description: A brief description of the product or service
    - target_users: A list of the intended users or customer segments for the product or service.

    - Ensure all required fields are filled with accurate information found in the URL content.

    - If any information is not available or cannot be found, indicate this in the respective field."""
    ...


async def safe_extract_company_domain(user_email: str | None) -> str | None:
    if not user_email:
        return None

    try:
        user_email_domain = safe_domain_from_email(user_email)
        if not user_email_domain:
            return None

        company_domain_classification = await run_classify_email_domain_agent(
            ClassifyEmailDomainAgentInput(email_domain=user_email_domain),
        )
        if company_domain_classification.result != ClassifyEmailDomainAgentOutput.Result.COMPANY_EMAIL_DOMAIN:
            return None

        return user_email_domain
    except workflowai.WorkflowAIError as e:
        _logger.exception("Error extracting company domain", exc_info=e)
        return None


async def safe_generate_company_description_from_email(
    user_email: str | None,
) -> ExtractCompanyInfoFromDomainTaskOutput | None:
    company_domain = await safe_extract_company_domain(user_email)
    if not company_domain:
        return None

    try:
        company_description = await _extract_company_info_from_domain(
            ExtractCompanyInfoFromDomainTaskInput(company_domain=company_domain),
            use_cache="always",
        )
    except workflowai.WorkflowAIError as e:
        _logger.exception("Error extracting company info from domain", exc_info=e)
        return None
    return company_description


async def safe_generate_company_description_from_domain(
    company_domain: str | None,
) -> ExtractCompanyInfoFromDomainTaskOutput | None:
    if not company_domain:
        return None
    return await _extract_company_info_from_domain(
        ExtractCompanyInfoFromDomainTaskInput(company_domain=company_domain),
        use_cache="always",
    )
