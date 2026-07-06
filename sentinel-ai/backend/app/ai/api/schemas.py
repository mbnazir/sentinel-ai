from pydantic import BaseModel


class InvestigationNarrativeResponse(BaseModel):
    case_id: str
    executive_summary: str
    key_findings: list[str]
    evidence_summary: list[str]
    recommended_next_steps: list[str]
    limitations: list[str]
