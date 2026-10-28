from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.employee_day import EmployeeDaySnapshot, load_employee_day
from app.core.database import get_db

router = APIRouter(prefix="/employee-days", tags=["employee-days"])


@router.get("/{agent_id}/{shift_date}", response_model=EmployeeDaySnapshot)
async def get_employee_day(
    agent_id: str,
    shift_date: date,
    ingestion_run_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> EmployeeDaySnapshot:
    result = await load_employee_day(
        db,
        ingestion_run_id=ingestion_run_id,
        agent_id=agent_id,
        shift_date=shift_date,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Employee day not found in ingestion run")
    return result
