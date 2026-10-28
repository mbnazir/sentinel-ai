from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.analytics.organization_models import OrganizationalAssessment
from app.analytics.organization_service import build_organizational_assessment
from app.core.database import get_db
router=APIRouter(prefix='/organization',tags=['organization'])
@router.get('/assessment',response_model=OrganizationalAssessment)
async def get_organizational_assessment(ingestion_run_id:UUID,date_from:date,date_to:date,db:AsyncSession=Depends(get_db))->OrganizationalAssessment:
    try:return await build_organizational_assessment(db,ingestion_run_id=ingestion_run_id,date_from=date_from,date_to=date_to)
    except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc
