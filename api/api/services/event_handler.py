import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Concatenate, Coroutine, Generic, NamedTuple, TypeVar

from taskiq import AsyncTaskiqDecoratedTask
from taskiq_redis import RedisScheduleSource

from api.jobs import features_by_domain_generation_started_jobs
from core.domain.analytics_events.analytics_events import OrganizationProperties, TaskProperties, UserProperties
from core.domain.events import (
    AIReviewCompletedEvent,
    AIReviewerBuildStartedEvent,
    AIReviewerUpdatedEvent,
    AIReviewStartedEvent,
    Event,
    EventRouter,
    FeaturesByDomainGenerationStarted,
    FeedbackCreatedEvent,
    MetaAgentChatMessagesSent,
    RecomputeReviewBenchmarkEvent,
    RunCreatedEvent,
    SendAnalyticsEvent,
    StoreTaskRunEvent,
    TaskChatStartedEvent,
    TaskGroupCreated,
    TaskGroupSaved,
    TaskInstructionsGeneratedEvent,
    TaskSchemaCreatedEvent,
    TaskSchemaGeneratedEvent,
    TenantCreatedEvent,
    TenantMigratedEvent,
    TriggerRunEvaluationEvent,
    TriggerTaskRunEvent,
    UserReviewAddedEvent,
)

_logger = logging.getLogger(__name__)


_T = TypeVar("_T", bound=Event)


class _JobListing(NamedTuple, Generic[_T]):
    event: type[_T]
    jobs: list[AsyncTaskiqDecoratedTask[Concatenate[_T, ...], Coroutine[Any, Any, None]]]  # Run ASAP
    scheduled_jobs: (
        list[tuple[AsyncTaskiqDecoratedTask[Concatenate[_T, ...], Coroutine[Any, Any, None]], timedelta]] | None
    ) = None


def _jobs():
    # Importing here to avoid circular dependency
    from api.jobs import (
        ai_review_completed_jobs,
        ai_review_started_jobs,
        ai_reviewer_build_started_jobs,
        ai_reviewer_updated_jobs,
        analytics_jobs,
        chat_started_jobs,
        feedback_created_jobs,
        meta_agent_chat_messages_sent_jobs,
        recompute_review_benchmark_jobs,
        run_created_jobs,
        store_run_jobs,
        task_group_created_jobs,
        task_group_saved_jobs,
        task_instructions_generated_jobs,
        task_schema_created_jobs,
        task_schema_generated_jobs,
        tenant_created_jobs,
        tenant_migrated_jobs,
        trigger_run_evaluation_jobs,
        trigger_task_run_jobs,
        user_review_added_jobs,
    )

    # We use an array to have correct typing
    return [
        _JobListing(RunCreatedEvent, run_created_jobs.JOBS),
        _JobListing(
            TaskSchemaCreatedEvent,
            task_schema_created_jobs.JOBS,
        ),
        _JobListing(
            TriggerTaskRunEvent,
            [
                trigger_task_run_jobs.trigger_run,
            ],
        ),
        _JobListing(SendAnalyticsEvent, analytics_jobs.jobs),
        _JobListing(TaskChatStartedEvent, chat_started_jobs.JOBS),
        _JobListing(TaskSchemaGeneratedEvent, task_schema_generated_jobs.JOBS),
        _JobListing(TaskGroupCreated, task_group_created_jobs.JOBS),
        _JobListing(StoreTaskRunEvent, store_run_jobs.JOBS),
        _JobListing(UserReviewAddedEvent, user_review_added_jobs.JOBS),
        _JobListing(AIReviewerUpdatedEvent, ai_reviewer_updated_jobs.JOBS),
        _JobListing(RecomputeReviewBenchmarkEvent, recompute_review_benchmark_jobs.JOBS),
        _JobListing(AIReviewStartedEvent, ai_review_started_jobs.JOBS),
        _JobListing(AIReviewCompletedEvent, ai_review_completed_jobs.JOBS),
        _JobListing(AIReviewerBuildStartedEvent, ai_reviewer_build_started_jobs.JOBS),
        _JobListing(TaskGroupSaved, task_group_saved_jobs.JOBS),
        _JobListing(TriggerRunEvaluationEvent, trigger_run_evaluation_jobs.JOBS),
        _JobListing(TaskInstructionsGeneratedEvent, task_instructions_generated_jobs.JOBS),
        _JobListing(MetaAgentChatMessagesSent, meta_agent_chat_messages_sent_jobs.JOBS),
        _JobListing(FeedbackCreatedEvent, feedback_created_jobs.JOBS),
        _JobListing(FeaturesByDomainGenerationStarted, features_by_domain_generation_started_jobs.JOBS),
        _JobListing(TenantCreatedEvent, tenant_created_jobs.JOBS),
        _JobListing(TenantMigratedEvent, tenant_migrated_jobs.JOBS, tenant_migrated_jobs.SCHEDULED_JOBS),
    ]


def _build_schedule_source():
    broker_url = os.environ["JOBS_BROKER_URL"]
    if broker_url.startswith("redis"):
        return RedisScheduleSource(broker_url)

    return None


_schedule_source = _build_schedule_source()


class _EventRouter:
    def __init__(self) -> None:
        self._tasks: set[asyncio.Task[None]] = set()
        self._handlers: dict[type[Event], _JobListing[Event]] = {job.event: job for job in _jobs()}  # pyright: ignore [reportAttributeAccessIssue]

    @classmethod
    async def _send_job(
        cls,
        job: AsyncTaskiqDecoratedTask[[_T], Coroutine[Any, Any, None]],
        event: _T,
        retry_after: datetime | None = None,
    ):
        try:
            if retry_after:
                if _schedule_source:
                    await job.schedule_by_time(_schedule_source, retry_after, event)
                    return

                    # If no schedule source is available, we sleep for the delay.
                    await asyncio.sleep((retry_after - datetime.now()).total_seconds())
            await job.kiq(event)
        except Exception as e:
            # We retry once, see https://github.com/redis/redis-py/issues/2491
            # We added the hiredis parser so this should not happen
            _logger.warning("Error sending job, retrying", exc_info=e)
            try:
                await job.kiq(event)
            except Exception:
                _logger.exception("Error sending job")

    def _schedule_task(
        self,
        job: AsyncTaskiqDecoratedTask[[Event], Coroutine[Any, Any, None]],
        event: Event,
        schedule_time: datetime | None,
    ):
        t = asyncio.create_task(self._send_job(job, event, schedule_time))
        self._tasks.add(t)
        t.add_done_callback(self._tasks.remove)

    def __call__(self, event: Event, retry_after: datetime | None = None) -> None:
        try:
            listing = self._handlers[type(event)]
            for job in listing.jobs:
                self._schedule_task(job, event, retry_after)

            if listing.scheduled_jobs:
                now = datetime.now()
                for job, delay in listing.scheduled_jobs:
                    self._schedule_task(job, event, now + delay)

        except KeyError as e:
            _logger.exception("Missing event handler", exc_info=e)
            return
        except Exception as e:
            # This one should never happen
            _logger.exception("Error handling event", exc_info=e)


_event_router = _EventRouter()


def system_event_router() -> EventRouter:
    return _event_router


def tenant_event_router(
    tenant: str,
    tenant_uid: int,
    user_properties: UserProperties | None,
    organization_properties: OrganizationProperties | None,
    task_properties: TaskProperties | None,
) -> EventRouter:
    def _tenant_event_router(event: Event, retry_after: datetime | None = None) -> None:
        event.tenant = tenant
        event.tenant_uid = tenant_uid
        event.user_properties = user_properties
        event.organization_properties = organization_properties
        event.task_properties = task_properties
        _event_router(event, retry_after)

    return _tenant_event_router
