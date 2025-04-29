from typing import Literal

from core.domain.models.providers import Provider
from core.providers.google.vertex_base_config import VertexBaseConfig


class GoogleImagenVertexConfig(VertexBaseConfig):
    provider: Literal[Provider.GOOGLE_IMAGEN] = Provider.GOOGLE_IMAGEN
