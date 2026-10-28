from datetime import date
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field

class BehavioralLevel(StrEnum):
    NORMAL="normal"; WATCH="watch"; ELEVATED="elevated"; HIGH="high"; CRITICAL="critical"

class DailyBehavior(BaseModel):
    model_config=ConfigDict(frozen=True)
    agent_id:str; shift_date:date; supervisor_id:str|None=None; campaign_id:str|None=None
    risk_score:float=Field(ge=0,le=100); finding_count:int=0; manual_gain_seconds:int=0
    rounded_additions:int=0; payroll_edits:int=0; supervisor_additions:int=0; manager_additions:int=0

class BehavioralFinding(BaseModel):
    model_config=ConfigDict(frozen=True)
    code:str; subject_type:str; subject_id:str; level:BehavioralLevel; score:float=Field(ge=0,le=100)
    reason:str; observed:float; baseline:float|None=None; sample_size:int=0; metadata:dict[str,object]=Field(default_factory=dict)

class BehavioralProfile(BaseModel):
    model_config=ConfigDict(frozen=True)
    subject_type:str; subject_id:str; date_from:date; date_to:date; days_observed:int
    total_manual_gain_seconds:int; average_daily_gain_seconds:float; high_risk_days:int
    behavioral_score:float=Field(ge=0,le=100); level:BehavioralLevel
    findings:tuple[BehavioralFinding,...]=()
