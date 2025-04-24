from datetime import date
from typing import NamedTuple


class DailyUserDigest(NamedTuple):
    for_date: date
    tenant_slug: str
    org_id: str | None
    remaining_credits_usd: float
    added_credits_usd: float

    class Agent(NamedTuple):
        name: str
        agent_id: str
        agent_schema_id: int
        description: str | None
        run_count_last_24h: int
        active_run_count_last_24h: int

    agents: list[Agent]


class DailyDigestAndEmail(NamedTuple):
    daily_digest: DailyUserDigest

    class Email(NamedTuple):
        subject: str | None = None
        body: str | None = None

    email: Email
