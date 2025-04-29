from typing import Literal, override

from core.domain.models.models import Model
from core.domain.models.providers import Provider
from core.providers.google.vertex_base_config import VertexBaseConfig
from core.providers.google_imagen.google_imagen_base_provider import GoogleImagenBaseProvider


class GoogleImagenVertexConfig(VertexBaseConfig):
    provider: Literal[Provider.GOOGLE_IMAGEN] = Provider.GOOGLE_IMAGEN


class GoogleImagenVertexProvider(GoogleImagenBaseProvider[GoogleImagenVertexConfig]):
    @override
    def _request_url(self, model: Model) -> str:
        region = self._config.get_random_location(self._get_metadata, self._add_metadata)
        return f"https://{region}-aiplatform.googleapis.com/v1/projects/{self._config.vertex_project}/locations/{region}/publishers/google/models/{model}:predict"

    @override
    async def _request_headers(self) -> dict[str, str]:
        return await self._config.get_request_headers()

    @override
    @classmethod
    def required_env_vars(cls) -> list[str]:
        return VertexBaseConfig.required_env_vars()

    @override
    @classmethod
    def name(cls) -> Provider:
        return Provider.GOOGLE_IMAGEN

    @override
    @classmethod
    def _default_config(cls, index: int) -> GoogleImagenVertexConfig:
        return GoogleImagenVertexConfig.default(index)

    @classmethod
    def sanitize_config(cls, config: GoogleImagenVertexConfig) -> GoogleImagenVertexConfig:
        return config.sanitize()
