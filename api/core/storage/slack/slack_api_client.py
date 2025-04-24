import logging
from typing import Any

import httpx
from pydantic import BaseModel, Field

from core.domain.errors import InternalError
from core.storage.slack.slack_types import SlackMessage

_logger = logging.getLogger(__name__)


class SlackApiClient:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token

    def _client(self):
        return httpx.AsyncClient(
            base_url="https://slack.com/api",
            headers={"Authorization": f"Bearer {self.bot_token}", "Content-Type": "application/json; charset=utf-8"},
        )

    def _check_response(
        self,
        response: httpx.Response,
        operation_name: str,
    ) -> dict[str, Any]:
        """Check if Slack API response has ok=True, log and possibly raise error if not"""
        parsed = response.json()
        response.raise_for_status()
        if not parsed.get("ok", False):
            error_msg = f"Slack client failed to {operation_name}"
            error = parsed.get("error", "Unknown error")

            raise InternalError(error_msg, extra={"error_msg": error})

        return parsed

    async def post(
        self,
        endpoint: str,
        json_data: dict[str, Any],
        operation_name: str,
    ) -> dict[str, Any]:
        """Make a POST request to Slack API and check response"""
        async with self._client() as client:
            response = await client.post(endpoint, json=json_data)

            return self._check_response(
                response,
                operation_name,
            )

    async def get(
        self,
        endpoint: str,
        params: dict[str, str],
        operation_name: str,
    ) -> dict[str, Any]:
        """Make a GET request to Slack API and check response"""
        async with self._client() as client:
            response = await client.get(endpoint, params=params)

            return self._check_response(
                response,
                operation_name,
            )

    async def create_channel(self, name: str) -> str:
        """Create a slack channel and return a channel id"""
        parsed = await self.post(
            "/conversations.create",
            json_data={"name": name, "is_private": False},
            operation_name="create slack channel",
        )
        return parsed["channel"]["id"]

    async def rename_channel(self, channel_id: str, name: str):
        """Rename a slack channel"""
        await self.post(
            "/conversations.rename",
            json_data={"channel": channel_id, "name": name},
            operation_name="rename slack channel",
        )

    async def invite_users(self, channel_id: str, user_ids: list[str]):
        """Invite users to a slack channel"""
        await self.post(
            "/conversations.invite",
            json_data={"channel": channel_id, "users": ",".join(user_ids)},
            operation_name="invite users to slack channel",
        )

    async def send_message(self, channel_id: str, message: SlackMessage) -> dict[str, Any]:
        """Send a message to a slack channel"""
        return await self.post(
            "/chat.postMessage",
            json_data={"channel": channel_id, **message},
            operation_name="send slack message",
        )

    # TODO: not user yet, we need to add 'pins:write' scope to the bot token
    async def send_pinned_message(self, channel_id: str, message: SlackMessage):
        """Send a message to a slack channel and pin it"""
        message_payload = await self.send_message(channel_id, message)
        await self.post(
            "/pins.add",
            json_data={"channel": channel_id, "timestamp": message_payload["ts"]},
            operation_name="pin slack message",
        )

    async def set_channel_topic(self, channel_id: str, topic: str):
        """Set the topic of a slack channel"""
        await self.post(
            "/conversations.setTopic",
            json_data={"channel": channel_id, "topic": topic},
            operation_name="set slack channel topic",
        )

    async def set_channel_purpose(self, channel_id: str, purpose: str):
        """Set the purpose of a slack channel"""
        await self.post(
            "/conversations.setPurpose",
            json_data={"channel": channel_id, "purpose": purpose},
            operation_name="set slack channel purpose",
        )

    class ChannelInfo(BaseModel):
        id: str
        name: str

        class Topic(BaseModel):
            value: str = ""

        topic: Topic = Field(default_factory=Topic)

        class Purpose(BaseModel):
            value: str = ""

        purpose: Purpose = Field(default_factory=Purpose)

    async def get_channel_info(self, channel_id: str):
        parsed = await self.get(
            "/conversations.info",
            params={"channel": channel_id},
            operation_name="get slack channel info",
        )
        return self.ChannelInfo.model_validate(parsed["channel"])

    async def list_channels(self, limit: int = 1000):
        parsed = await self.get(
            "/conversations.list",
            params={"exclude_archived": "true", "limit": str(limit)},
            operation_name="list slack channels",
        )
        return [self.ChannelInfo.model_validate(channel) for channel in parsed["channels"]]
