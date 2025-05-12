from api.dependencies.event_router import EventRouterDep
from api.dependencies.services import GroupServiceDep, RunServiceDep
from api.dependencies.storage import StorageDep
from api.services.models import ModelsService
from core.domain.consts import WORKFLOWAI_APP_URL
from core.domain.errors import BadRequestError


class OpenAIProxyService:
    def __init__(
        self,
        group_service: GroupServiceDep,
        storage: StorageDep,
        run_service: RunServiceDep,
        event_router: EventRouterDep,
    ):
        self._group_service = group_service
        self._storage = storage
        self._run_service = run_service
        self._event_router = event_router

    @classmethod
    async def missing_model_error(cls, model: str | None):
        _check_lineup = f"Check the lineup 👉 {WORKFLOWAI_APP_URL}/models (25+ models)"
        if not model:
            return BadRequestError(
                f"""Empty model
{_check_lineup}""",
            )

        components = [
            f"Unknown model: {model}",
            _check_lineup,
        ]
        if suggested := await ModelsService.suggest_model(model):
            components.insert(1, f"Did you mean {suggested}?")
        return BadRequestError("\n".join(components))
