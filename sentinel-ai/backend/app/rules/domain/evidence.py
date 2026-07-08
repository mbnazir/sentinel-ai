from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Evidence:
    evidence_type: str
    payload: dict[str, Any]
