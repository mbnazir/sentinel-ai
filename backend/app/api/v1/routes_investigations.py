from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from kombu.exceptions import OperationalError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import Principal, current_principal
from app.core.database import get_db
from app.infrastructure.models import AnalysisScanModel, DurableFindingModel, InvestigationAuditEventModel, InvestigationCaseModel
from app.investigations.models import AuditEvent, CaseCreate, CaseUpdate, DurableFinding, InvestigationCase, ScanCreate, ScanRecord
from app.investigations.service import create_case, create_scan, update_case
from app.workers.celery_app import celery_app

router = APIRouter(tags=["investigations"])


@router.post("/scans", response_model=ScanRecord, status_code=201)
async def post_scan(
    payload: ScanCreate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(current_principal),
) -> ScanRecord:
    if payload.scope == "historical_comparison":
        # Comparison provenance must identify the authenticated investigator,
        # not an actor name supplied in the request body.
        payload = payload.model_copy(update={"requested_by": principal.subject})
    if payload.eligibility_mode.value == "OBSERVED_RECORDS_ONLY" and principal.role.value not in {
        "manager", "admin"
    }:
        raise HTTPException(
            status_code=403,
            detail="OBSERVED_RECORDS_ONLY requires manager or admin authorization",
        )
    try:
        scan = await create_scan(db, payload, actor_role=principal.role.value)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        celery_app.send_task("app.workers.tasks.execute_scan", args=[str(scan.id)])
    except (OperationalError, OSError) as exc:
        # create_scan may already have committed this record. Do not silently
        # claim dispatch succeeded or create a duplicate by automatic retry.
        raise HTTPException(
            status_code=503,
            detail=f"Scan {scan.id} was created, but task dispatch failed. Check its status before retrying.",
        ) from exc

    return ScanRecord.model_validate(scan)


@router.post("/scans/{scan_id}/cancel", response_model=ScanRecord)
async def cancel_scan(scan_id: UUID, db: AsyncSession = Depends(get_db)) -> ScanRecord:
    scan = await db.get(AnalysisScanModel, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="scan not found")
    if scan.status in {"completed", "failed", "cancelled"}:
        raise HTTPException(status_code=409, detail=f"scan is already {scan.status}")
    scan.cancel_requested = True
    await db.commit()
    await db.refresh(scan)
    return ScanRecord.model_validate(scan)


@router.get("/scans/{scan_id}", response_model=ScanRecord)
async def get_scan(scan_id: UUID, db: AsyncSession = Depends(get_db)) -> ScanRecord:
    scan = await db.get(AnalysisScanModel, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="scan not found")
    return ScanRecord.model_validate(scan)


@router.get("/scans/{scan_id}/findings", response_model=list[DurableFinding])
async def get_scan_findings(scan_id: UUID, db: AsyncSession = Depends(get_db)) -> list[DurableFinding]:
    result = await db.execute(select(DurableFindingModel).where(DurableFindingModel.scan_id == scan_id))
    return [DurableFinding.model_validate(item) for item in result.scalars().all()]


@router.post("/investigations", response_model=InvestigationCase, status_code=201)
async def post_case(payload: CaseCreate, db: AsyncSession = Depends(get_db)) -> InvestigationCase:
    try:
        return InvestigationCase.model_validate(await create_case(db, payload))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/investigations/{case_id}", response_model=InvestigationCase)
async def patch_case(case_id: UUID, payload: CaseUpdate, db: AsyncSession = Depends(get_db)) -> InvestigationCase:
    try:
        return InvestigationCase.model_validate(await update_case(db, case_id, payload))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/investigations/{case_id}", response_model=InvestigationCase)
async def get_case(case_id: UUID, db: AsyncSession = Depends(get_db)) -> InvestigationCase:
    case = await db.get(InvestigationCaseModel, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")
    return InvestigationCase.model_validate(case)


@router.get("/investigations/{case_id}/audit", response_model=list[AuditEvent])
async def get_case_audit(case_id: UUID, db: AsyncSession = Depends(get_db)) -> list[AuditEvent]:
    result = await db.execute(
        select(InvestigationAuditEventModel)
        .where(InvestigationAuditEventModel.case_id == case_id)
        .order_by(InvestigationAuditEventModel.created_at.asc())
    )
    return [AuditEvent.model_validate(item) for item in result.scalars().all()]
