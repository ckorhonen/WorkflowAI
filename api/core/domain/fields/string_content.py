from pydantic import BaseModel


class StringContent(BaseModel):
    content: str
