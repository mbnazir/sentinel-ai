from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.timeline.analysis import EmployeeDayAnalysis, analyze_employee_day
from app.timeline.builder import load_employee_day_timeline
from app.timeline.models import EmployeeDayTimeline

router = APIRouter(prefix="/timelines", tags=["timelines"])


@router.get("/{agent_id}/{shift_date}", response_model=EmployeeDayTimeline)
async def get_timeline(
    agent_id: str,
    shift_date: date,
    ingestion_run_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> EmployeeDayTimeline:
    timeline = await load_employee_day_timeline(
        db,
        ingestion_run_id=ingestion_run_id,
        agent_id=agent_id,
        shift_date=shift_date,
    )
    if timeline is None:
        raise HTTPException(status_code=404, detail="Employee day not found in ingestion run")
    return timeline


@router.get("/{agent_id}/{shift_date}/analysis", response_model=EmployeeDayAnalysis)
async def get_timeline_analysis(
    agent_id: str,
    shift_date: date,
    ingestion_run_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> EmployeeDayAnalysis:
    timeline = await load_employee_day_timeline(
        db,
        ingestion_run_id=ingestion_run_id,
        agent_id=agent_id,
        shift_date=shift_date,
    )
    if timeline is None:
        raise HTTPException(status_code=404, detail="Employee day not found in ingestion run")
    return analyze_employee_day(timeline)
