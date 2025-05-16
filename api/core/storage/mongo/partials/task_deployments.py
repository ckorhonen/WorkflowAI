from collections.abc import Iterable
from typing import Any, AsyncIterator

from core.domain.task_deployment import TaskDeployment
from core.domain.version_environment import VersionEnvironment
from core.storage import TenantTuple
from core.storage.mongo.models.deployment_document import TaskDeploymentDocument
from core.storage.mongo.mongo_types import AsyncCollection
from core.storage.mongo.partials.base_partial_storage import PartialStorage
from core.storage.mongo.utils import projection


class MongoTaskDeploymentsStorage(PartialStorage[TaskDeploymentDocument]):
    def __init__(self, tenant: TenantTuple, collection: AsyncCollection):
        super().__init__(tenant, collection, TaskDeploymentDocument)

    @property
    def _object_type(self) -> str:
        return "deployment"

    async def list_task_deployments(
        self,
        task_id: str,
        task_schema_id: int | None = None,
        environment: VersionEnvironment | None = None,
        iteration: int | None = None,
        exclude: Iterable[str] | None = None,
    ) -> AsyncIterator[TaskDeployment]:
        filter: dict[str, Any] = {}
        filter["task_id"] = task_id
        if task_schema_id:
            filter["task_schema_id"] = task_schema_id
        if environment:
            filter["environment"] = environment
        if iteration:
            filter["iteration"] = iteration
        deployments = self._find(filter, sort=[("deployed_at", -1)], projection=projection(exclude=exclude))
        async for deployment in deployments:
            yield deployment.to_resource()

    async def get_task_deployment(
        self,
        task_id: str,
        task_schema_id: int,
        environment: VersionEnvironment,
    ) -> TaskDeployment:
        deployment = await self._find_one(
            {"task_id": task_id, "task_schema_id": task_schema_id, "environment": environment},
        )
        return deployment.to_resource()

    async def get_task_deployment_for_iteration(self, task_id: str, iteration: int) -> AsyncIterator[TaskDeployment]:
        deployments = self._find({"task_id": task_id, "iteration": iteration})
        async for deployment in deployments:
            yield deployment.to_resource()

    async def deploy_task_version(self, deployment: TaskDeployment) -> TaskDeploymentDocument:
        set_value = TaskDeploymentDocument.from_resource(self.tenant, deployment).set_value()
        return await self._find_one_and_update(
            {
                "task_id": deployment.task_id,
                "task_schema_id": deployment.schema_id,
                "environment": deployment.environment,
            },
            {"$set": set_value},
            upsert=True,
            return_document=True,
        )

    async def get_task_deployed_versions_ids(self, task_id: str) -> set[int]:
        return set(await self._distinct("version_id", {"task_id": task_id}))
