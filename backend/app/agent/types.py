from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal, Protocol


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    name: str
    args: dict[str, Any]
    id: str | None = None


@dataclass(frozen=True)
class ToolResult:
    name: str
    output: dict[str, Any]


@dataclass(frozen=True)
class Turn:
    role: Literal["user", "model", "tool"]
    text: str | None = None
    tool_calls: tuple[ToolCall, ...] = ()
    tool_results: tuple[ToolResult, ...] = ()
    raw: Any = None  # provider-specific payload, replayed verbatim (e.g. Gemini thought signatures)


@dataclass(frozen=True)
class LLMResponse:
    text: str | None = None
    tool_calls: tuple[ToolCall, ...] = ()
    raw: Any = None


class ProviderError(Exception):
    pass


class ProviderQuotaError(ProviderError):
    pass


class LLMProvider(Protocol):
    def generate(self, system: str, historico: Sequence[Turn], tools: Sequence[ToolSpec]) -> LLMResponse: ...
