from dataclasses import dataclass


@dataclass(frozen=True)
class AIResponse:
    content: str
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
