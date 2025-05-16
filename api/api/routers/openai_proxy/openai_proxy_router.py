from fastapi import APIRouter, Request, Response

from api.dependencies.event_router import EventRouterDep
from api.dependencies.security import RequiredUserOrganizationDep
from api.dependencies.services import GroupServiceDep, RunServiceDep
from api.dependencies.storage import StorageDep
from api.routers.openai_proxy._openai_proxy_handler import OpenAIProxyHandler

from ._openai_proxy_models import (
    OpenAIProxyChatCompletionChunk,
    OpenAIProxyChatCompletionRequest,
    OpenAIProxyChatCompletionResponse,
)

router = APIRouter(prefix="", tags=["openai"])


@router.post(
    "/v1/chat/completions",
    responses={
        200: {
            "content": {
                "text/event-stream": {
                    "schema": OpenAIProxyChatCompletionChunk.model_json_schema(),
                },
                "application/json": {
                    "schema": OpenAIProxyChatCompletionResponse.model_json_schema(),
                },
            },
        },
    },
)
async def chat_completions(
    body: OpenAIProxyChatCompletionRequest,
    group_service: GroupServiceDep,
    storage: StorageDep,
    run_service: RunServiceDep,
    event_router: EventRouterDep,
    request: Request,
    user_org: RequiredUserOrganizationDep,
) -> Response:
    body.check_supported_fields()

    handler = OpenAIProxyHandler(group_service, storage, run_service, event_router)
    return await handler.handle(body, request, user_org)
