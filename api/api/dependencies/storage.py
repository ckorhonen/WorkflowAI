from typing import Annotated

from fastapi import Depends

from api.dependencies.encryption import EncryptionDep
from api.dependencies.event_router import EventRouterDep
from api.dependencies.security import FinalTenantDataDep, TenantUIDDep
from api.services import storage
from core.storage.backend_storage import BackendStorage
from core.storage.key_value_storage import KeyValueStorage
from core.storage.organization_storage import OrganizationStorage
from core.storage.reviews_storage import ReviewsStorage
from core.storage.task_group_storage import TaskGroupStorage
from core.storage.task_input_storage import TaskInputsStorage
from core.storage.transcription_storage import TranscriptionStorage


def storage_dependency(
    tenant: FinalTenantDataDep,
    encryption: EncryptionDep,
    event_router: EventRouterDep,
) -> BackendStorage:
    return storage.storage_for_tenant(tenant.tenant, tenant.uid, event_router, encryption)


StorageDep = Annotated[BackendStorage, Depends(storage_dependency)]


def task_group_storage_dependency(storage: StorageDep) -> TaskGroupStorage:
    return storage.task_groups


TaskGroupStorageDep = Annotated[TaskGroupStorage, Depends(task_group_storage_dependency)]


def task_input_storage_dependency(storage: StorageDep) -> TaskInputsStorage:
    return storage.task_inputs


TaskInputsStorageDep = Annotated[TaskInputsStorage, Depends(task_input_storage_dependency)]


def organization_storage_dependency(storage: StorageDep) -> OrganizationStorage:
    return storage.organizations


OrganizationStorageDep = Annotated[OrganizationStorage, Depends(organization_storage_dependency)]


def transcription_storage_dependency(storage: StorageDep) -> TranscriptionStorage:
    return storage.transcriptions


TranscriptionStorageDep = Annotated[TranscriptionStorage, Depends(transcription_storage_dependency)]


def reviews_storage_dependency(storage: StorageDep) -> ReviewsStorage:
    return storage.reviews


ReviewsStorageDep = Annotated[ReviewsStorage, Depends(reviews_storage_dependency)]


def key_value_storage_dependency(tenant_uid: TenantUIDDep) -> KeyValueStorage:
    return storage.key_value_storage_for_tenant(tenant_uid)


KeyValueStorageDep = Annotated[KeyValueStorage, Depends(key_value_storage_dependency)]
