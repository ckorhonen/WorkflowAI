from fastapi import APIRouter

from api.tags import RouteTags

router = APIRouter(prefix="/_mcp", tags=[RouteTags.MCP])
"""A specific router for MCP. This way we can maintain routes separately."""
