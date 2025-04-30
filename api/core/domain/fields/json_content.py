from typing import Any

from pydantic import BaseModel


class JSONContent(BaseModel):
    content: dict[str, Any] | list[Any]
