from dataclasses import dataclass


@dataclass(frozen=True)
class InvestigationNarrative:
    case_id: str
    executive_summary: str
    key_findings: list[str]
    evidence_summary: list[str]
    recommended_next_steps: list[str]
    limitations: list[str]
    raw_model_output: str
