from datetime import datetime

import pytest
from pytest_mock import MockerFixture

from api.dependencies.task_ban import check_task_banned_dependency
from core.domain.ban import Ban
from core.domain.task_info import TaskInfo
from core.providers.base.provider_error import TaskBannedError


async def test_check_task_banned_not_banned(mocker: MockerFixture) -> None:
    await check_task_banned_dependency(
        TaskInfo(
            task_id="task_123",
            name="",
            is_public=False,
            ban=None,
        ),
    )


async def test_check_task_banned_is_banned(mocker: MockerFixture) -> None:
    # Act & Assert
    with pytest.raises(TaskBannedError):
        await check_task_banned_dependency(
            TaskInfo(
                task_id="task_123",
                name="",
                is_public=False,
                ban=Ban(
                    banned_at=datetime.now(),
                    reason="task_run_non_compliant",
                    related_ids=["run1"],
                ),
            ),
        )
