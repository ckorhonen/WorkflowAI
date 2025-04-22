import logging
import os

from fastapi import APIRouter, HTTPException, Request

from api.tags import RouteTags
from core.storage.slack.slack_api_client import SlackApiClient

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/slack-webhooks", tags=[RouteTags.WEBHOOKS])


@router.post("")
async def slack_webhook(request: Request):
    try:
        payload = await request.json()
        _logger.info("Received Slack webhook", extra={"payload": payload})
        # Handle Slack URL verification
        if "challenge" in payload:
            return {"challenge": payload["challenge"]}

        slack_client = SlackApiClient(bot_token=os.environ["SLACK_BOT_TOKEN"])
        await slack_client.handle_webhook(payload)

        return {"status": "success"}
    except Exception as e:
        _logger.exception("Error processing Slack webhook", extra={"error": e})
        raise HTTPException(status_code=400, detail=str(e))
