from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.connector_factory import UnsupportedConnectorError, build_connector
from app.application.ingestion import IngestionRangeError, SnapshotIngestionService
from app.connectors.quartz import QuartzRestConnector
from app.core.auth import Principal, current_principal
from app.core.database import get_db
from app.infrastructure.models import (ActivitySnapshotModel, ConnectorModel,
    IngestionActivityBatchModel, IngestionProgressModel, IngestionRunModel,
    SessionSnapshotModel)
from app.workers.tasks import execute_ingestion

router = APIRouter(prefix="/ingestion-runs", tags=["ingestion"])


def _legacy_failure_category(message: str | None) -> str | None:
    if not message:
        return "legacy_failure_unclassified"
    normalized = message.casefold()
    if "timeout" in normalized or "timed out" in normalized:
        return "read_timeout"
    for status_code in (429, 502, 503, 504):
        if f"http {status_code}" in normalized:
            return f"http_{status_code}"
    if "401" in normalized or "unauthorized" in normalized:
        return "http_401"
    return "legacy_failure_unclassified"


class IngestionCreate(BaseModel):
    connector_id: UUID
    shift_date_from: date
    shift_date_to: date
    idempotency_key: str = Field(min_length=8, max_length=128)
    # Testing / controlled ingestion
    max_sessions: int | None = Field(default=None, ge=1, le=10000)


class IngestionRead(BaseModel):
    id: UUID
    connector_id: UUID
    idempotency_key: str
    shift_date_from: date
    shift_date_to: date
    status: str
    session_count: int
    activity_count: int
    error_message: str | None


class IngestionProgressRead(BaseModel):
    ingestion_run_id: UUID
    run_exists: bool = True
    run_status: str
    checkpoint_availability: str
    recovery_eligible: bool
    recovery_attempt_count: int
    recovery_initialized_at: datetime | None
    recovery_initialized_by: str | None
    existing_session_snapshots: int
    existing_activity_snapshots: int
    lease_state: str
    completion_status: str
    reconciliation_status: str
    session_collection_complete: bool
    persisted_unique_sessions: int
    expected_sessions: int | None
    completed_activity_sessions: int
    persisted_activities: int
    expected_activities: int | None
    activity_batch_count: int
    completed_activity_batches: int
    failed_activity_batches: int
    date_coverage: dict[str, object]
    reconciliation: dict[str, object]
    last_failure_category: str | None


@router.post(
    "",
    response_model=IngestionRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_ingestion_run(
    payload: IngestionCreate,
    db: AsyncSession = Depends(get_db),
) -> IngestionRead:

    connector_row = await db.get(
        ConnectorModel,
        payload.connector_id,
    )

    if connector_row is None:
        raise HTTPException(
            status_code=404,
            detail="Connector not found",
        )

    if not connector_row.enabled:
        raise HTTPException(
            status_code=409,
            detail="Connector is disabled",
        )

    existing = await db.scalar(
        select(IngestionRunModel).where(
            IngestionRunModel.connector_id
            == payload.connector_id,
            IngestionRunModel.idempotency_key
            == payload.idempotency_key,
        )
    )

    if existing is not None:
        return _to_read(existing)

    run = IngestionRunModel(
        connector_id=payload.connector_id,
        idempotency_key=payload.idempotency_key,
        shift_date_from=payload.shift_date_from,
        shift_date_to=payload.shift_date_to,
        status="queued",
        session_count=0,
        activity_count=0,
    )

    db.add(run)
    await db.commit()
    await db.refresh(run)

    execute_ingestion.delay(
        str(run.id),
        payload.max_sessions,
    )

    return _to_read(run)

@router.get("", response_model=list[IngestionRead])
async def list_ingestion_runs(db: AsyncSession = Depends(get_db)) -> list[IngestionRead]:
    result = await db.execute(
        select(IngestionRunModel).order_by(IngestionRunModel.started_at.desc()).limit(100)
    )
    return [_to_read(row) for row in result.scalars()]


@router.get("/{run_id}", response_model=IngestionRead)
async def get_ingestion_run(
    run_id: UUID, db: AsyncSession = Depends(get_db)
) -> IngestionRead:
    row = await db.get(IngestionRunModel, run_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Ingestion run not found")
    return _to_read(row)


@router.get("/{run_id}/progress", response_model=IngestionProgressRead)
async def get_ingestion_progress(run_id: UUID, db: AsyncSession = Depends(get_db)) -> IngestionProgressRead:
    run = await db.get(IngestionRunModel, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Ingestion run not found")
    progress = await db.get(IngestionProgressModel, run_id)
    sessions = int(await db.scalar(select(func.count()).select_from(SessionSnapshotModel)
                                   .where(SessionSnapshotModel.ingestion_run_id == run_id)) or 0)
    activities = int(await db.scalar(select(func.count()).select_from(ActivitySnapshotModel)
                                     .where(ActivitySnapshotModel.ingestion_run_id == run_id)) or 0)
    if progress is None:
        return IngestionProgressRead(
            ingestion_run_id=run_id, run_status=run.status,
            checkpoint_availability="LEGACY_MISSING", recovery_eligible=run.status == "failed",
            recovery_attempt_count=0, recovery_initialized_at=None, recovery_initialized_by=None,
            existing_session_snapshots=sessions, existing_activity_snapshots=activities,
            lease_state="NOT_INITIALIZED", completion_status="UNVERIFIED",
            reconciliation_status="UNVERIFIED", session_collection_complete=False,
            persisted_unique_sessions=sessions, expected_sessions=None,
            completed_activity_sessions=0, persisted_activities=activities,
            expected_activities=None, activity_batch_count=0, completed_activity_batches=0,
            failed_activity_batches=0, date_coverage={},
            reconciliation={"reason": "Legacy run has no durable checkpoints; historical page coverage is unknown"},
            last_failure_category=_legacy_failure_category(run.error_message)
            if run.status == "failed" else None)
    result = await db.execute(select(IngestionActivityBatchModel).where(
        IngestionActivityBatchModel.ingestion_run_id == run_id))
    batches = list(result.scalars())
    lease_state = ("ACTIVE" if progress.lease_expires_at and progress.lease_expires_at > datetime.now(UTC)
                   else "EXPIRED" if progress.lease_expires_at else "NONE")
    return IngestionProgressRead(
        ingestion_run_id=run_id, run_status=run.status,
        checkpoint_availability="AVAILABLE",
        recovery_eligible=(run.status == "failed" and not progress.recovery_initialized_at
                           and lease_state != "ACTIVE"),
        recovery_attempt_count=progress.recovery_attempt_count,
        recovery_initialized_at=progress.recovery_initialized_at,
        recovery_initialized_by=progress.recovery_initialized_by,
        existing_session_snapshots=sessions, existing_activity_snapshots=activities,
        lease_state=lease_state,
        completion_status=progress.completion_status,
        reconciliation_status=progress.reconciliation_status,
        session_collection_complete=progress.session_collection_complete,
        persisted_unique_sessions=progress.sessions_persisted_count,
        expected_sessions=progress.expected_session_count,
        completed_activity_sessions=progress.sessions_with_completed_activities,
        persisted_activities=progress.activities_persisted_count,
        expected_activities=progress.expected_activity_count,
        activity_batch_count=len(batches),
        completed_activity_batches=sum(batch.status == "completed" for batch in batches),
        failed_activity_batches=sum(batch.status == "failed" for batch in batches),
        date_coverage=progress.date_coverage_json or {},
        reconciliation=progress.reconciliation_json or {},
        last_failure_category=progress.last_failure_category)


@router.post("/{run_id}/recovery-initialize", response_model=IngestionProgressRead)
async def initialize_legacy_recovery(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(current_principal),
) -> IngestionProgressRead:
    # Router-level authorization restricts this endpoint to manager/admin.
    run = await db.scalar(select(IngestionRunModel).where(
        IngestionRunModel.id == run_id).with_for_update())
    if run is None:
        raise HTTPException(status_code=404, detail="Ingestion run not found")
    if run.status != "failed":
        raise HTTPException(status_code=409, detail="Recovery initialization requires a failed run")
    progress = await db.get(IngestionProgressModel, run_id)
    if progress is not None:
        if progress.recovery_initialized_at is not None:
            await db.commit()
            return await get_ingestion_progress(run_id, db)
        raise HTTPException(status_code=409, detail="Run already has checkpoints; use controlled resume")
    snapshot_counts = {
        "sessions": int(await db.scalar(select(func.count()).select_from(SessionSnapshotModel)
            .where(SessionSnapshotModel.ingestion_run_id == run_id)) or 0),
        "activities": int(await db.scalar(select(func.count()).select_from(ActivitySnapshotModel)
            .where(ActivitySnapshotModel.ingestion_run_id == run_id)) or 0),
    }
    progress = IngestionProgressModel(
        ingestion_run_id=run_id, completion_status="INCOMPLETE",
        reconciliation_status="INCOMPLETE", recovery_attempt_count=1,
        recovery_initialized_at=datetime.now(UTC), recovery_initialized_by=principal.subject,
        last_failure_category="legacy_recovery_initialized",
        reconciliation_json={"reason": "Legacy page coverage unknown; source records must be re-fetched",
                             "snapshot_counts_at_initialization": snapshot_counts})
    db.add(progress)
    await db.commit()
    return await get_ingestion_progress(run_id, db)


@router.post("/{run_id}/resume", response_model=IngestionRead, status_code=status.HTTP_202_ACCEPTED)
async def resume_ingestion_run(run_id: UUID, db: AsyncSession = Depends(get_db),
                               principal: Principal = Depends(current_principal)) -> IngestionRead:
    run = await db.scalar(select(IngestionRunModel).where(
        IngestionRunModel.id == run_id).with_for_update())
    if run is None:
        raise HTTPException(status_code=404, detail="Ingestion run not found")
    if run.status not in {"failed", "partial"}:
        raise HTTPException(status_code=409, detail="Only failed or partial runs can be resumed")
    progress = await db.get(IngestionProgressModel, run_id)
    if progress is None:
        raise HTTPException(status_code=409, detail="Legacy run requires recovery initialization first")
    if progress.lease_expires_at and progress.lease_expires_at > datetime.now(UTC):
        raise HTTPException(status_code=409, detail="Ingestion worker currently holds the run lease")
    if progress.recovery_initialized_at is not None:
        progress.recovery_attempt_count += 1
        progress.recovery_initialized_at = datetime.now(UTC)
        progress.recovery_initialized_by = principal.subject
    run.status = "queued"
    run.error_message = None
    await db.commit()
    execute_ingestion.delay(str(run.id), None)
    return _to_read(run)


def _to_read(row: IngestionRunModel) -> IngestionRead:
    return IngestionRead(
        id=row.id,
        connector_id=row.connector_id,
        idempotency_key=row.idempotency_key,
        shift_date_from=row.shift_date_from,
        shift_date_to=row.shift_date_to,
        status=row.status,
        session_count=row.session_count,
        activity_count=row.activity_count,
        error_message=row.error_message,
    )
