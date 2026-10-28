from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.models import InvestigatorSummary
from app.ai.service import summarize_case
from app.core.auth import Principal, current_principal
from app.core.database import get_db
from app.infrastructure.models import AIInvestigatorSummaryModel

router=APIRouter(prefix="/ai",tags=["ai-investigator"])

@router.post("/investigations/{case_id}/summary",response_model=InvestigatorSummary)
async def create_summary(case_id:UUID,principal:Principal=Depends(current_principal),db:AsyncSession=Depends(get_db)):
    try:
        row=await summarize_case(db,case_id,principal.subject)
        return InvestigatorSummary.model_validate(row)
    except LookupError as exc:
        raise HTTPException(status_code=404,detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503,detail=str(exc)) from exc

@router.get("/investigations/{case_id}/summary",response_model=InvestigatorSummary|None)
async def latest_summary(case_id:UUID,db:AsyncSession=Depends(get_db)):
    result=await db.execute(select(AIInvestigatorSummaryModel).where(AIInvestigatorSummaryModel.case_id==case_id).order_by(AIInvestigatorSummaryModel.created_at.desc()).limit(1))
    row=result.scalar_one_or_none()
    return None if row is None else InvestigatorSummary.model_validate(row)
