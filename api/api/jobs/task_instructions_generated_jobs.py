import logging

from api.jobs.common import (
    InternalTasksServiceDep,
    StorageDep,
)
from core.domain.events import AgentInstructionsGeneratedEvent

from ..broker import broker

logger = logging.getLogger(__name__)


@broker.task(retry_on_error=True)
async def create_task_description_and_image(
    event: AgentInstructionsGeneratedEvent,
    storage: StorageDep,
    internal_tasks: InternalTasksServiceDep,
):
    # We trigger the task description generation based on the instructions we generated ourselves, to enforce the format:
    # The descriptions for tasks should mirror the content of the opening line of instructions we generate, minus the "You are…" at the start. So:
    # Opening line: You are a medical scribe assistant specializing in converting medical transcripts into structured SOAP notes. -> Task description: A medical scribe assistant specializing in converting medical transcripts into structured SOAP notes.
    # See: https://linear.app/workflowai/issue/WOR-3234/rework-task-descriptions

    async for _ in internal_tasks.set_task_description_if_missing(
        task_id=event.task_id,
        task_schema_id=event.task_schema_id,
        instructions=event.agent_instructions,
    ):
        # TODO: Convert generate_task_description into an unary function if we do no need the generator in the future
        pass


JOBS = [create_task_description_and_image]
