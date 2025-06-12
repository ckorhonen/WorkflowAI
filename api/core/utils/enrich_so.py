import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List

import httpx
from pydantic import BaseModel


class DateInfo(BaseModel):
    month: int | None = None
    year: int | None = None


class StartEndDate(BaseModel):
    start: DateInfo | None = None
    end: DateInfo | None = None


class Position(BaseModel):
    startEndDate: StartEndDate | None = None
    title: str | None = None
    companyName: str | None = None
    companyLogo: str | None = None
    linkedInUrl: str | None = None
    employmentType: str | None = None


class Positions(BaseModel):
    positionsCount: int | None = None
    positionHistory: List[Position] | None = None


class Education(BaseModel):
    startEndDate: StartEndDate | None = None
    schoolName: str | None = None
    description: str | None = None
    degreeName: str | None = None
    fieldOfStudy: str | None = None
    schoolLogo: str | None = None
    linkedInUrl: str | None = None


class Schools(BaseModel):
    educationsCount: int | None = None
    educationHistory: List[Education] | None = None


class EnrichSoEnrichedEmailData(BaseModel):
    connectionCount: int | None = None
    creationDate: Dict[str, int] | None = None
    displayName: str | None = None
    firstName: str | None = None
    followerCount: int | None = None
    headline: str | None = None
    summary: str | None = None
    lastName: str | None = None
    linkedInIdentifier: str | None = None
    linkedInUrl: str | None = None
    location: str | None = None
    phoneNumbers: List[Any] | None = None
    photoUrl: str | None = None
    positions: Positions | None = None
    schools: Schools | None = None
    publicIdentifier: str | None = None
    skills: List[str] | None = None
    email: str | None = None
    total_credits: int | None = None
    credits_used: int | None = None
    credits_remaining: int | None = None

    @property
    def full_name(self) -> str | None:
        if self.firstName and self.lastName:
            return f"{self.firstName} {self.lastName}"
        return self.firstName or self.lastName


@asynccontextmanager
async def _enrich_client():
    api_key = os.environ.get("ENRICH_SO_API_KEY")
    if not api_key:
        logging.getLogger(__name__).warning("ENRICH_SO_API_KEY is not set")
        return

    async with httpx.AsyncClient(
        base_url="https://api.enrich.so/v1/api",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    ) as client:
        yield client


async def get_enriched_email_data(user_email: str) -> EnrichSoEnrichedEmailData | None:
    async with _enrich_client() as client:
        response = await client.get(
            "/person",
            params={
                "email": user_email,
            },
            timeout=60.0,
        )

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None
        raise e

    return EnrichSoEnrichedEmailData.model_validate(response.json())


class Founded(BaseModel):
    month: int | None = None
    day: int | None = None
    year: int | None = None


class StaffRange(BaseModel):
    start: int | None = None
    end: int | None = None


class Staff(BaseModel):
    total: int | None = None
    size: str | None = None
    range: StaffRange | None = None


class Urls(BaseModel):
    company_page: str | None = None
    li_url: str | None = None


class Images(BaseModel):
    logo: str | None = None
    cover: str | None = None


class CallToAction(BaseModel):
    url: str | None = None
    text: str | None = None


class Location(BaseModel):
    country: str | None = None
    geographic_area: str | None = None
    city: str | None = None
    postal_code: str | None = None
    line1: str | None = None
    line2: str | None = None
    description: str | None = None


class Locations(BaseModel):
    headquarter: Location | None = None
    other: List[Location] | None = None


class MoneyRaised(BaseModel):
    currency: str | None = None
    amount: int | None = None


class FundingDate(BaseModel):
    month: int | None = None
    day: int | None = None
    year: int | None = None


class Investor(BaseModel):
    investor_url: str | None = None
    logo: str | None = None
    name: str | None = None


class LastFundingRound(BaseModel):
    funding_type: str | None = None
    money_raised: MoneyRaised | None = None
    announced_on: FundingDate | None = None
    lead_investors: List[Investor] | None = None
    num_of_other_investors: int | None = None
    round_url: str | None = None


class FundingData(BaseModel):
    num_of_funding_rounds: int | None = None
    last_funding_round: LastFundingRound | None = None
    organization_url: str | None = None
    funding_rounds_url: str | None = None


class EnrichSoEnrichedCompanyData(BaseModel):
    name: str | None = None
    universal_name: str | None = None
    company_id: int | None = None
    description: str | None = None
    phone: str | None = None
    followers: int | None = None
    urls: Urls | None = None
    website: str | None = None
    industries: List[str] | None = None
    images: Images | None = None
    tagline: str | None = None
    founded: Founded | None = None
    type: str | None = None
    staff: Staff | None = None
    call_to_action: CallToAction | None = None
    locations: Locations | None = None
    specialities: List[str] | None = None
    funding_data: FundingData | None = None
    hashtags: List[str] | None = None
    total_credits: int | None = None
    credits_used: int | None = None
    credits_remaining: int | None = None


async def get_enriched_company_profile_data(linkedin_company_domain: str) -> EnrichSoEnrichedCompanyData | None:
    async with _enrich_client() as client:
        response = await client.get(
            "/linkedin-by-url",
            params={
                "url": linkedin_company_domain,
                "type": "company",
            },
            timeout=60.0,
        )

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None
        raise e

    return EnrichSoEnrichedCompanyData.model_validate(response.json())
