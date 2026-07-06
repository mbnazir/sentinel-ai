from enum import StrEnum


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def score_weight(self) -> int:
        return {
            Severity.LOW: 10,
            Severity.MEDIUM: 25,
            Severity.HIGH: 50,
            Severity.CRITICAL: 80,
        }[self]
