import logging
import time
from datetime import datetime
from typing import Any

from api.services.groups import GroupService
from api.services.run import RunService
from core.domain.analytics_events.analytics_events import RunTrigger
from core.domain.errors import (
    InternalError,
    ProviderRateLimitError,
    ProviderUnavailableError,
    ServerOverloadedError,
)
from core.domain.events import EventRouter, RecomputeReviewBenchmarkEvent, TriggerTaskRunEvent
from core.domain.task_run_query import SerializableTaskRunQuery
from core.domain.types import AgentInput
from core.domain.users import UserIdentifier
from core.domain.version_reference import VersionReference
from core.storage import ObjectNotFoundException, TaskTuple
from core.storage.backend_storage import BackendStorage
from core.utils.uuid import uuid7


class BackgroundRunService:
    def __init__(
        self,
        run_service: RunService,
        storage: BackendStorage,
        event_router: EventRouter,
        group_service: GroupService,
        user: UserIdentifier | None,
    ):
        self._storage = storage
        self._event_router = event_router
        self._logger = logging.getLogger(self.__class__.__name__)
        self.group_service = group_service
        self.user = user
        self._run_service = run_service

    async def _fetch_task_input(
        self,
        task_id: TaskTuple,
        task_schema_id: int,
        task_input_hash: str | None,
        task_input: AgentInput | None,
    ) -> AgentInput:
        if task_input is not None:
            return task_input

        if not task_input_hash:
            raise InternalError("Either task_input or task_input_hash must be provided")

        try:
            full_task_input = await self._storage.task_inputs.get_input_by_hash(
                task_id[0],
                task_schema_id,
                task_input_hash,
            )
            return full_task_input.task_input or {}
        except ObjectNotFoundException:
            pass

        # Otherwise we fetch a run with the same input hash
        query = SerializableTaskRunQuery(
            task_id=task_id[0],
            task_schema_id=task_schema_id,
            task_input_hashes={task_input_hash},
            limit=1,
            include_fields={"task_input"},
            status={"success"},
        )
        try:
            run = await anext(self._storage.task_runs.fetch_task_run_resources(task_uid=task_id[1], query=query))
            return run.task_input
        except StopAsyncIteration:
            raise ObjectNotFoundException(
                f"Agent input with hash {task_input_hash} not found",
                code="agent_input_not_found",
            )

    async def _insert_in_review_benchmark_if_needed(
        self,
        task_id: str,
        task_schema_id: int,
        iteration: int,
        trigger: RunTrigger,
        run_id: str,
    ):
        if not trigger == "review_benchmark":
            return

        try:
            await self._storage.review_benchmarks.add_in_progress_run(task_id, task_schema_id, iteration, run_id)
        except Exception:
            self._logger.exception(
                "Failed to add in progress run to review benchmark",
                extra={"task_id": task_id, "task_schema_id": task_schema_id, "iteration": iteration},
            )

    async def _update_review_benchmark_for_run(
        self,
        task_id: str,
        task_schema_id: int,
        iteration: int,
        run_id: str | None,
        trigger: RunTrigger,
        cached_run_id: str | None,
    ):
        if not trigger == "review_benchmark":
            return

        self._event_router(
            RecomputeReviewBenchmarkEvent(
                task_id=task_id,
                task_schema_id=task_schema_id,
                run_id=run_id,
                iterations={iteration},
                cached_run_id=cached_run_id,
            ),
        )

    async def _retry_run_if_possible(
        self,
        task_id: str,
        task_schema_id: int,
        task_input_hash: str | None,
        task_input: dict[str, Any] | None,
        iteration: int,
        trigger: RunTrigger,
        run_id: str,
        retry_count: int,
        retry_after: datetime | None,
    ):
        if retry_count < 3:
            self._event_router(
                event=TriggerTaskRunEvent(
                    task_id=task_id,
                    task_schema_id=task_schema_id,
                    group_iteration=iteration,
                    task_input_hash=task_input_hash,
                    task_input=task_input,
                    run_id=run_id,
                    trigger=trigger,
                    retry_count=retry_count + 1,
                ),
                retry_after=retry_after,
            )
            return True
        return False

    async def _run_from_cache(
        self,
        task_id: TaskTuple,
        task_schema_id: int,
        task_input_hash: str | None,
        group_hash: str,
    ):
        if not task_input_hash:
            # This is likely never true so just adding a warning for now
            self._logger.warning("No task input hash provided, cannot run from cache")
            return None

        return await self._storage.task_runs.fetch_cached_run(
            task_id=task_id,
            task_schema_id=task_schema_id,
            task_input_hash=task_input_hash,
            group_id=group_hash,
            timeout_ms=None,
            success_only=False,
        )

    async def run_for_trigger(
        self,
        task_id: str,
        task_schema_id: int,
        group_iteration: int,
        task_input: dict[str, Any] | None,
        task_input_hash: str | None,
        run_id: str | None,
        trigger: RunTrigger,
        retry_count: int,
    ):
        task_group = await self._storage.task_groups.get_task_group_by_iteration(
            task_id,
            task_schema_id,
            group_iteration,
        )

        runner, is_different_version = await self.group_service.sanitize_groups_for_internal_runner(
            task_id,
            task_schema_id,
            VersionReference(properties=task_group.properties),
        )
        # Here the final group could be different from the requested group, for example if a model has been sunset
        # This will lead to errors when updating the benchmark but it's safer that simply not running the task
        if is_different_version:
            self._logger.warning(
                "Task group properties have changed, running with updated properties",
                extra={"task_id": task_id, "task_schema_id": task_schema_id, "group_iteration": group_iteration},
            )
            # Saving the new group so we can get the iteration
            # TODO[iteration]: this will no longer be needed once we use the group hash directly
            saved_group = await self._storage.get_or_create_task_group(
                task_id,
                task_schema_id,
                runner.properties,
                tags=[],
                user=self.user,
            )
            group_iteration = saved_group.iteration

        manual_cache = trigger == "review_benchmark"
        id_tuple = runner.task.id_tuple
        if manual_cache:
            # First we try and find a run that matches the input and group hash
            # We are bypassing the automatic cache to allow re-using failed runs
            if run := await self._run_from_cache(
                id_tuple,
                task_schema_id,
                task_input_hash,
                runner.properties.model_hash(),
            ):
                await self._update_review_benchmark_for_run(
                    task_id,
                    task_schema_id,
                    group_iteration,
                    None,
                    trigger,
                    cached_run_id=run.id,
                )
                return

        # Fetch task input if not provided
        task_input = await self._fetch_task_input(id_tuple, task_schema_id, task_input_hash, task_input)

        if not run_id:
            run_id = str(uuid7())

        await self._insert_in_review_benchmark_if_needed(task_id, task_schema_id, group_iteration, trigger, run_id)

        # TODO: we should likely bypass the run cache and compute the cache manually
        # To allow re-using failed runs
        cached_run_id: str | None = None
        try:
            builder = await runner.task_run_builder(task_input, task_run_id=run_id, start_time=time.time())
            run = await self._run_service.run_from_builder(
                builder,
                runner=runner,
                trigger=trigger,
                store_inline=False,
                cache="never" if manual_cache else "auto",
            )
            if run.from_cache:
                cached_run_id = run.id

        except (ProviderRateLimitError, ServerOverloadedError, ProviderUnavailableError) as e:
            # We retry on rate limits
            # We do not use the normal retry mechanic to propagate the run id
            if await self._retry_run_if_possible(
                task_id,
                task_schema_id,
                task_input_hash,
                task_input,
                group_iteration,
                trigger,
                run_id,
                retry_count,
                e.retry_after_date(),
            ):
                return
            raise e
        finally:
            await self._update_review_benchmark_for_run(
                task_id,
                task_schema_id,
                group_iteration,
                run_id,
                trigger,
                cached_run_id=cached_run_id,
            )
