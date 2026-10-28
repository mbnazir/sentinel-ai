from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.rules.engine import IntegrityRuleEngine
from app.rules.models import RiskAssessment
from app.timeline.analysis import analyze_employee_day
from app.timeline.builder import load_employee_day_timeline

router = APIRouter(prefix="/assessments", tags=["assessments"])
engine = IntegrityRuleEngine()


@router.get("/{agent_id}/{shift_date}", response_model=RiskAssessment)
async def get_integrity_assessment(
    agent_id: str,
    shift_date: date,
    ingestion_run_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> RiskAssessment:
    timeline = await load_employee_day_timeline(
        db,
        ingestion_run_id=ingestion_run_id,
        agent_id=agent_id,
        shift_date=shift_date,
    )
    if timeline is None:
        raise HTTPException(status_code=404, detail="Employee day not found in ingestion run")
    analysis = analyze_employee_day(timeline)
    return engine.evaluate(analysis)
