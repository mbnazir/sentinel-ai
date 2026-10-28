from datetime import date
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field
from app.analytics.models import DailyBehavior

class OrganizationalLevel(StrEnum):
    NORMAL="normal"
    WATCH="watch"
    ELEVATED="elevated"
    HIGH="high"
    CRITICAL="critical"

class OrganizationalDailyBehavior(DailyBehavior):
    manager_id: str | None = None
    client_id: str | None = None
    site_id: str | None = None
    team_id: str | None = None
    payroll_adjustments: int = 0
    manager_interventions: int = 0

class RelationshipFinding(BaseModel):
    model_config=ConfigDict(frozen=True)
    code:str
    relationship_type:str
    subject_ids:tuple[str,...]
    level:OrganizationalLevel
    score:float=Field(ge=0,le=100)
    reason:str
    event_count:int
    distinct_shift_dates:int
    affected_agents:int=0
    metadata:dict[str,object]=Field(default_factory=dict)

class GroupRiskProfile(BaseModel):
    model_config=ConfigDict(frozen=True)
    group_type:str
    group_id:str
    date_from:date
    date_to:date
    employee_days:int
    distinct_agents:int
    manual_gain_seconds:int
    high_risk_days:int
    payroll_adjustment_days:int
    score:float=Field(ge=0,le=100)
    level:OrganizationalLevel
    findings:tuple[RelationshipFinding,...]=()

class OrganizationalAssessment(BaseModel):
    model_config=ConfigDict(frozen=True)
    date_from:date
    date_to:date
    employee_days_analyzed:int
    distinct_agents:int
    supervisor_profiles:tuple[GroupRiskProfile,...]=()
    manager_profiles:tuple[GroupRiskProfile,...]=()
    campaign_profiles:tuple[GroupRiskProfile,...]=()
    site_profiles:tuple[GroupRiskProfile,...]=()
    relationship_findings:tuple[RelationshipFinding,...]=()
    data_quality_notes:tuple[str,...]=()
