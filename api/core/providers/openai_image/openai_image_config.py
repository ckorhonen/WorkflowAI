from pydantic import BaseModel

from core.domain.models.providers import Provider


class OpenAIImageConfig(BaseModel):
    api_key: str

    @property
    def provider(self) -> Provider:
        return Provider.OPEN_AI_IMAGE
