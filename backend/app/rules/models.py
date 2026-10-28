from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.evidence.models import EvidenceItem


class RuleSeverity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingCategory(StrEnum):
    INTEGRITY = "integrity"
    WORKFLOW = "workflow"
    PAYROLL = "payroll"
    COLLUSION = "collusion"
    DATA_QUALITY = "data_quality"


class RuleFinding(BaseModel):
    model_config = ConfigDict(frozen=True)

    rule_id: str
    rule_name: str
    category: FindingCategory
    severity: RuleSeverity
    source_session_id: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    risk_contribution: float = Field(ge=0.0, le=100.0)
    reason: str
    evidence: tuple[EvidenceItem, ...] = ()
    metadata: dict[str, object] = Field(default_factory=dict)


class RiskLevel(StrEnum):
    NORMAL = "normal"
    REVIEW = "review"
    SUSPICIOUS = "suspicious"
    HIGH = "high"
    CRITICAL = "critical"


class RiskAssessment(BaseModel):
    model_config = ConfigDict(frozen=True)

    risk_score: float = Field(ge=0.0, le=100.0)
    risk_level: RiskLevel
    finding_count: int
    critical_count: int
    high_count: int
    findings: tuple[RuleFinding, ...]
    mitigating_notes: tuple[str, ...] = ()
