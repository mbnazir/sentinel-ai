from dataclasses import dataclass
from enum import StrEnum


class TrendDirection(StrEnum):
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass(frozen=True)
class BehaviorMetric:
    name: str
    value: float
    unit: str | None = None


@dataclass(frozen=True)
class TrendResult:
    metric_name: str
    direction: TrendDirection
    slope: float
    first_value: float
    last_value: float
    change_percent: float
