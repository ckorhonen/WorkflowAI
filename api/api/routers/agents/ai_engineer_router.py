from typing import Annotated, AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from api.dependencies.event_router import EventRouterDep
from api.dependencies.services import (
    ModelsServiceDep,
    ReviewsServiceDep,
    RunsServiceDep,
    StorageDep,
    VersionsServiceDep,
)
from api.routers.feedback_v1 import FeedbackServiceDep
from api.services.internal_tasks.meta_agent_service import (
    MetaAgentChatMessage,
    MetaAgentService,
)
from core.utils.stream_response_utils import safe_streaming_response

router = APIRouter(prefix="/agents/ai-engineer")


def meta_agent_service_dependency(
    storage: StorageDep,
    event_router: EventRouterDep,
    runs_service: RunsServiceDep,
    models_service: ModelsServiceDep,
    feedback_service: FeedbackServiceDep,
    versions_service: VersionsServiceDep,
    reviews_service: ReviewsServiceDep,
):
    return MetaAgentService(
        storage=storage,
        event_router=event_router,
        runs_service=runs_service,
        models_service=models_service,
        feedback_service=feedback_service,
        versions_service=versions_service,
        reviews_service=reviews_service,
    )


MetaAgentServiceDep = Annotated[MetaAgentService, Depends(meta_agent_service_dependency)]


class MetaAgentChatRequest(BaseModel):
    messages: list[MetaAgentChatMessage] = Field(
        description="The list of messages in the conversation, the last message being the most recent one",
    )


class MetaAgentChatResponse(BaseModel):
    messages: list[MetaAgentChatMessage] = Field(
        description="The list of messages that compose the response of the meta-agent",
    )


@router.post(
    "/messages",
    description="To chat with WorkflowAI's meta agent",
    responses={
        200: {
            "content": {
                "text/event-stream": {
                    "schema": MetaAgentChatResponse.model_json_schema(),
                },
            },
        },
    },
)
async def get_meta_agent_chat(
    request: MetaAgentChatRequest,
    meta_agent_service: MetaAgentServiceDep,
) -> StreamingResponse:
    async def _stream() -> AsyncIterator[BaseModel]:
        async for messages in meta_agent_service.stream_ai_engineer_without_agent_id_response(
            messages=request.messages,
        ):
            yield MetaAgentChatResponse(messages=messages)

    return safe_streaming_response(_stream)
