from pydantic import BaseModel, ConfigDict, Field

class ScanSummary(BaseModel):
    model_config=ConfigDict(frozen=True)
    employee_days:int
    deterministic_findings:int
    behavioral_findings:int
    organizational_findings:int
    total_findings:int
    high_or_critical:int
    max_risk_score:float=Field(ge=0,le=100)
