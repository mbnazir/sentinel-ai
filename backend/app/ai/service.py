import hashlib, json
from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.providers import GeminiProvider, OpenAICompatibleProvider
from app.core.config import settings
from app.infrastructure.models import (
    AIInvestigatorSummaryModel,
    CaseFindingModel,
    DurableFindingModel,
    InvestigationAuditEventModel,
    InvestigationCaseModel,
)

PROMPT_VERSION="sentinel-investigator-v1"

def _provider():
    if settings.ai_provider=="gemini":
        if not settings.gemini_api_key: raise RuntimeError("GEMINI_API_KEY is not configured")
        return GeminiProvider(api_key=settings.gemini_api_key,model=settings.ai_model),settings.ai_model
    if settings.ai_provider=="openai":
        if not settings.openai_api_key: raise RuntimeError("OPENAI_API_KEY is not configured")
        return OpenAICompatibleProvider(base_url=settings.openai_base_url,api_key=settings.openai_api_key,model=settings.ai_model),settings.ai_model
    raise RuntimeError("AI_PROVIDER must be gemini or openai")

async def summarize_case(db:AsyncSession,case_id:UUID,actor:str):
    case=await db.get(InvestigationCaseModel,case_id)
    if case is None: raise LookupError("case not found")
    result=await db.execute(select(DurableFindingModel).join(CaseFindingModel,CaseFindingModel.finding_id==DurableFindingModel.id).where(CaseFindingModel.case_id==case_id).order_by(DurableFindingModel.risk_contribution.desc()))
    findings=list(result.scalars())
    payload={"case":{"case_number":case.case_number,"title":case.title,"status":case.status,"disposition":case.disposition},
      "findings":[{"rule_id":f.rule_id,"severity":f.severity,"confidence":f.confidence,"risk_contribution":f.risk_contribution,"agent_id":f.agent_id,"shift_date":str(f.shift_date) if f.shift_date else None,"session_id":f.source_session_id,"reason":f.reason,"evidence":f.evidence_json} for f in findings]}
    canonical=json.dumps(payload,sort_keys=True,separators=(",",":"),default=str)
    input_hash=hashlib.sha256(canonical.encode()).hexdigest()
    provider,model=_provider()
    prompt="Create an investigator brief with sections: Executive Summary, Observed Facts, Repeated Patterns, Data Quality / Limitations, Review Questions, Recommended Next Steps. Do not infer facts not present. Evidence follows:\n"+json.dumps(payload,indent=2,default=str)
    narrative=await provider.summarize(prompt)
    row=AIInvestigatorSummaryModel(
        id=uuid4(),case_id=case_id,provider=settings.ai_provider,model=model,
        prompt_version=PROMPT_VERSION,input_hash=input_hash,narrative=narrative,
        requested_by=actor,created_at=datetime.now(timezone.utc)
    )
    db.add(row)
    db.add(InvestigationAuditEventModel(
        id=uuid4(),case_id=case_id,actor=actor,event_type="ai_summary_generated",
        event_json={"provider":settings.ai_provider,"model":model,"prompt_version":PROMPT_VERSION,"input_hash":input_hash},
    ))
    await db.commit(); await db.refresh(row)
    return row
