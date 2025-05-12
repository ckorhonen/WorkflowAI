from collections.abc import Callable, Coroutine
from typing import Any, Literal

type CacheUsage = Literal["auto", "always", "never", "when_available", "only"]
# when_available & only are deprecated

AgentInput = dict[str, Any]
AgentOutput = str | list[Any] | dict[str, Any]

TemplateRenderer = Callable[[str | None], Coroutine[Any, Any, str | None]]
