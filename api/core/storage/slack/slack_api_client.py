import datetime
import logging
from typing import Any

import httpx
from pydantic import BaseModel, Field

from core.agents.customer_success_helper_chat import CustomerSuccessHelperChatAgentInput, customer_success_helper_chat
from core.domain.errors import InternalError
from core.domain.fields.chat_message import ChatMessage
from core.storage.slack.slack_types import OutboundSlackMessage, SlackMessage, SlackWebhookEvent
from core.utils.redis_lock import LockAcquisitionError, redis_lock

_logger = logging.getLogger(__name__)

# Lock expiration time in seconds
WEBHOOK_LOCK_EXPIRY = 60


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
        params: dict[str, Any],
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

    async def send_message(self, channel_id: str, message: OutboundSlackMessage) -> dict[str, Any]:
        """Send a message to a slack channel"""
        return await self.post(
            "/chat.postMessage",
            json_data={"channel": channel_id, **message},
            operation_name="send slack message",
        )

    # TODO: not user yet, we need to add 'pins:write' scope to the bot token
    async def send_pinned_message(self, channel_id: str, message: OutboundSlackMessage):
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

    async def fetch_channel_messages(self, channel_id: str, limit: int = 100) -> list[SlackMessage]:
        """Fetch messages from a slack channel"""
        parsed = await self.get(
            "/conversations.history",
            params={"channel": channel_id, "limit": limit},
            operation_name="fetch slack channel messages",
        )
        messages: list[SlackMessage] = []
        for message in parsed["messages"][::-1]:  # reverse the order to have older messages at the begining of the list
            try:
                messages.append(SlackMessage(**message))
            except Exception as e:
                _logger.exception("Failed to parse slack message", extra={"message_payload": message}, exc_info=e)
        return messages

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

    def _should_process_webhook_event(self, webhook_event: SlackWebhookEvent) -> bool:
        bot_id: str | None = None

        # Filter out message that do not contain "@WorkflowAI Bot"
        if len(webhook_event.authorizations) > 0:
            # TODO: use an env var to store the bot id
            bot_id = webhook_event.authorizations[0].user_id

            if webhook_event.event and webhook_event.event.text and bot_id not in webhook_event.event.text:
                _logger.info(
                    "The message is not addressed to the bot, skipping",
                    extra={"event": webhook_event.event.text},
                )
                return False

        # Filter messages send by the bot itself
        if webhook_event.is_bot_triggered():
            _logger.info("Skipping bot triggered event", extra={"event": webhook_event})
            return False

        # Filter out non-message events (will be handled later, maybe)
        if webhook_event.event.type != "message":
            _logger.info("Skipping non-message event", extra={"event": webhook_event.event})
            return False

        return True

    async def handle_webhook(self, raw_payload: dict[str, Any]) -> None:
        try:
            # Parse the payload as a SlackWebhookEvent
            webhook_event = SlackWebhookEvent(**raw_payload)
            if not self._should_process_webhook_event(webhook_event=webhook_event):
                return

            # We need to implement a Redis lock mechanism because events are sometimes sent 2-3 times by Slack
            client_msg_id = getattr(webhook_event.event, "client_msg_id", None)
            if not client_msg_id:
                _logger.warning(
                    "No client_msg_id found in event, processing without lock",
                    extra={"event": webhook_event.event},
                )
            else:
                lock_key = f"slack:webhook:lock:{client_msg_id}"
                try:
                    async with redis_lock(lock_key, expire_seconds=60):
                        # Process the message only if we obtained the lock
                        await self._process_webhook_message(webhook_event)
                        return
                except LockAcquisitionError:
                    # This message is already being processed or was processed recently
                    _logger.info("Skipping duplicate webhook event", extra={"client_msg_id": client_msg_id})
                    return

            await self._process_webhook_message(webhook_event)

        except Exception as e:
            _logger.exception("Failed to handle Slack webhook", extra={"payload": raw_payload, "error": e})

    async def _process_webhook_message(self, webhook_event: SlackWebhookEvent) -> None:
        """Process a webhook message after deduplication check"""
        channel_id = webhook_event.event.channel

        messages = await self.fetch_channel_messages(channel_id)

        csm_agent_input = CustomerSuccessHelperChatAgentInput(
            messages=[
                ChatMessage(
                    role="ASSISTANT" if "bot_id" in message else "USER",
                    content=message["text"] or "not text in this message",
                )
                for message in messages
                if "text" in message
            ],
            current_datetime=datetime.datetime.now(),
        )

        csm_agent_run = await customer_success_helper_chat(csm_agent_input)

        await self.send_message(
            channel_id,
            OutboundSlackMessage(text=csm_agent_run.response or "no response from "),
        )
