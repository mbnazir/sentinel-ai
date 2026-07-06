from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AIMessage:
    role: str
    content: str


@dataclass(frozen=True)
class AIRequest:
    messages: list[AIMessage]
    temperature: float = 0.1
    max_tokens: int = 1200
    metadata: dict[str, Any] = field(default_factory=dict)
