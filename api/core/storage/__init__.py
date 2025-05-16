from typing import Any, TypeAlias

from core.domain.error_response import ErrorCode
from core.domain.errors import InternalError


# TODO: duplicate of ObjectNotFoundError, we should use only one of them
class ObjectNotFoundException(InternalError):
    default_code: ErrorCode = "object_not_found"

    def __init__(
        self,
        msg: str | None = None,
        code: ErrorCode | None = None,
        object_type: str | None = None,
        **extras: Any,
    ):
        super().__init__(msg, object_type=object_type, **extras)
        self.code: ErrorCode = code or self.default_code

    @property
    def object_type(self) -> str | None:
        return self.extras.get("object_type")


# TODO[ids]: passing as a tuple for now to reduce the amount of changes needed
# We should eventually  only use the int
TenantTuple: TypeAlias = tuple[str, int]
TaskTuple: TypeAlias = tuple[str, int]
