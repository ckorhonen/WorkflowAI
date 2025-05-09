from typing import Annotated

from fastapi import Depends

from api.dependencies.task_info import TaskInfoDep
from core.providers.base.provider_error import TaskBannedError


async def check_task_banned_dependency(
    task_info: TaskInfoDep,
) -> None:
    """Dependency that checks if a task is banned and raises 403 if it is"""
    if task_info is None:
        return
    if task_info.ban is not None:
        raise TaskBannedError()


CheckTaskBannedDep = Annotated[None, Depends(check_task_banned_dependency)]
