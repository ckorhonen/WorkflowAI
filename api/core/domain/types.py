from typing import Any, Literal

type CacheUsage = Literal["auto", "always", "never", "when_available", "only"]
# when_available & only are deprecated

AgentInput = dict[str, Any]
AgentOutput = str | list[Any] | dict[str, Any]
