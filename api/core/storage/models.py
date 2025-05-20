# A file to store models that are exposed by the storage layer
# These are not meant to be used unless communicating with the storage layer


from datetime import datetime

from pydantic import BaseModel

from core.domain.ban import Ban
from core.domain.integration.integration_domain import IntegrationKind


class TaskUpdate(BaseModel):
    is_public: bool | None = None
    name: str | None = None
    description: str | None = None
    hide_schema: int | None = None
    unhide_schema: int | None = None
    schema_last_active_at: tuple[int, datetime] | None = None
    ban: Ban | None = None
    used_integration_kind: IntegrationKind | None = None
