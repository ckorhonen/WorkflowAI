import asyncio
import os
from collections.abc import Awaitable, Callable
from typing import Annotated

import typer
from dotenv import load_dotenv

from _common import PROD_ARG, STAGING_ARG, get_mongo_storage
from core.domain.tenant_data import PublicOrganizationData
from core.services.customers.customer_service import CustomerService
from core.services.users.clerk_user_service import ClerkUserService
from core.services.users.user_service import UserService
from core.storage import ObjectNotFoundException
from core.storage.slack.slack_api_client import SlackApiClient


class Fixer:
    def __init__(
        self,
        slack_client: SlackApiClient,
        customer_service: CustomerService,
        user_service: UserService,
        get_by_slug: Callable[[str], Awaitable[PublicOrganizationData]],
    ):
        self.slack_client = slack_client
        self.customer_service = customer_service
        self.user_service = user_service
        self.get_by_slug = get_by_slug

    async def fix_purposes(self, limit: int = 2):
        channels = await self.slack_client.list_channels()
        for channel in channels:
            if not channel.name.startswith("customer-"):
                continue
            name = channel.name.removeprefix("customer-")
            if name.startswith("staging") or name.startswith("prod-preview"):
                print(f"Skipping {name} because it's not in prod")
                # Channels created not in prod so we can ignore
                continue

            # Now the name is the tenant slug

            if "dashboard.clerk.com" in channel.topic.value:
                print(f"Skipping {name} because there is already a clerk link")
                continue

            print(f"Fixing {name}")

            try:
                org = await self.get_by_slug(name)
            except ObjectNotFoundException:
                # Might be that we need to add an @
                try:
                    org = await self.get_by_slug(f"@{name}")
                except ObjectNotFoundException:
                    print(f"Organization not found for {name}")
                    continue

            user = await self.user_service.get_user(org.owner_id) if org.owner_id else None
            org = await self.user_service.get_organization(org.org_id) if org.org_id else None

            await self.customer_service._update_channel_purpose(  # type: ignore
                self.slack_client,
                channel.id,
                org.slug if org else name,
                user,
                org,
            )
            # Sleeping to avoid rate limiting on clerk endpoints
            await asyncio.sleep(1)

            limit -= 1
            if limit == 0:
                return


def main(
    prod: PROD_ARG,
    staging: STAGING_ARG,
    limit: Annotated[int, typer.Option()] = 2,
):
    load_dotenv(override=True)
    mongo_storage = get_mongo_storage(prod=prod, staging=staging, tenant="__system__")
    user_service = ClerkUserService(os.environ["CLERK_SECRET_KEY"])
    asyncio.run(
        Fixer(
            SlackApiClient(os.environ["SLACK_BOT_TOKEN"]),
            CustomerService(mongo_storage, user_service),
            user_service,
            mongo_storage.organizations.get_public_organization,
        ).fix_purposes(limit),
    )


if __name__ == "__main__":
    typer.run(main)
