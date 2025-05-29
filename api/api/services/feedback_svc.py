import asyncio
import base64
import hashlib
import hmac
import logging
import os
from collections.abc import Callable

from pydantic import BaseModel, Field

from core.domain.errors import BadRequestError
from core.domain.events import EventRouter, FeedbackCreatedEvent
from core.domain.feedback import Feedback, FeedbackAnnotation, FeedbackOutcome
from core.domain.page import Page, T
from core.storage.feedback_storage import FeedbackStorage, FeedbackSystemStorage
from core.utils.strings import safe_b64decode

_logger = logging.getLogger(__name__)


class FeedbackToken(BaseModel):
    tenant_uid: int = Field(alias="t")
    task_uid: int = Field(alias="u")
    run_id: str = Field(alias="r")


class FeedbackTokenGenerator:
    def __init__(self, key: bytes | None):
        if not key:
            _logger.warning("No key provided for feedback token generation, feedback tokens will not be signed")
        self._key = key

    def _hmac(self, bs: bytes):
        if not self._key:
            return None
        return hmac.new(self._key, bs, hashlib.sha256).digest()

    def generate_token(self, tenant_uid: int, task_uid: int, run_id: str) -> str:
        payload = FeedbackToken(
            t=tenant_uid,
            u=task_uid,
            r=run_id,
        )
        dumped = payload.model_dump_json(by_alias=True).encode()
        token = base64.b64encode(dumped).decode()

        if mac := self._hmac(dumped):
            return token + "." + base64.b64encode(mac).decode()

        return token

    def verify_token(self, token: str):
        splits = token.split(".")
        try:
            decoded = base64.b64decode(splits[0])
            payload = FeedbackToken.model_validate_json(decoded)
        except Exception as e:
            raise ValueError("Invalid token payload") from e

        if mac := self._hmac(decoded):
            if not len(splits) == 2:
                try:
                    sign = base64.b64decode(splits[1])
                except Exception as e:
                    raise ValueError("Could not decode token signature") from e
                if not hmac.compare_digest(mac, sign):
                    raise ValueError("Invalid token signature")

        return payload

    @classmethod
    def default_generator(cls):
        return cls(key=safe_b64decode(os.getenv("STORAGE_HMAC")))


class FeedbackService:
    def __init__(self, storage: FeedbackStorage):
        self.storage = storage

    @classmethod
    async def create_feedback(
        cls,
        feedback_storage: FeedbackSystemStorage,
        token_validator: Callable[[str], FeedbackToken],
        feedback_token: str,
        outcome: FeedbackOutcome,
        comment: str | None,
        user_id: str | None,
        event_router: EventRouter,
    ) -> Feedback:
        try:
            payload = token_validator(feedback_token)
        except ValueError as e:
            raise BadRequestError("Invalid feedback token", capture=True) from e

        # We could check if the run and task exist here, but since the token is supposedly signed
        # we should be good

        feedback = Feedback(
            run_id=payload.run_id,
            outcome=outcome,
            comment=comment,
            user_id=user_id,
        )
        stored = await feedback_storage.store_feedback(payload.tenant_uid, payload.task_uid, feedback)

        event_router(
            FeedbackCreatedEvent(
                tenant_uid=payload.tenant_uid,
                task_uid=payload.task_uid,
                feedback_id=stored.id,
                run_id=payload.run_id,
                outcome=outcome,
                comment=comment,
                user_id=user_id,
            ),
        )

        return stored

    @classmethod
    async def get_feedback(
        cls,
        feedback_storage: FeedbackSystemStorage,
        token_validator: Callable[[str], FeedbackToken],
        feedback_token: str,
        user_id: str | None,
    ):
        try:
            payload = token_validator(feedback_token)
        except ValueError as e:
            raise BadRequestError("Invalid feedback token", capture=True) from e

        return await feedback_storage.get_feedback(payload.tenant_uid, payload.task_uid, payload.run_id, user_id)

    async def list_feedback(
        self,
        task_uid: int,
        run_id: str | None,
        limit: int,
        offset: int,
        map_fn: Callable[[Feedback], T],
    ) -> Page[T]:
        async def _list():
            return [map_fn(feedback) async for feedback in self.storage.list_feedback(task_uid, run_id, limit, offset)]

        feedback_list, count = await asyncio.gather(_list(), self.storage.count_feedback(task_uid, run_id))

        return Page(items=feedback_list, count=count)

    def annotate_feedback(self, feedback_id: str, annotation: FeedbackAnnotation):
        return self.storage.add_annotation(feedback_id, annotation)
