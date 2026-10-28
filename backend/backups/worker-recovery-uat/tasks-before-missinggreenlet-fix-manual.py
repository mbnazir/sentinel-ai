import asyncio
import os
from datetime import datetime, timezone
from uuid import UUID, uuid4
from celery import shared_task
from sqlalchemy import func, select, text
from app.application.connector_factory import build_connector
from app.application.ingestion import SnapshotIngestionService
from app.connectors.quartz.rest import QuartzRestConnector
from app.core.database import get_session_factory, get_engine
from app.finalization.service import scan_is_ready_for_finalization, summarize_scan
from app.infrastructure.models import (
    AnalysisScanModel,
    ConnectorModel,
    DurableFindingModel,
    IngestionRunModel,
    ScanChunkModel,
    SessionSnapshotModel,
)
from app.investigations.models import ScanStatus
from app.workers.chunking import split_date_range
from app.workers.pipeline import ENGINE_VERSION, RULE_VERSION, process_employee_day
@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def execute_scan(self, scan_id: str):
    return asyncio.run(
        _execute_scan(UUID(scan_id), self.request.hostname or os.getenv("HOSTNAME", "worker"))
    )
@shared_task(bind=True, name="app.workers.tasks.execute_ingestion")
def execute_ingestion(self, run_id: str, max_sessions: int | None = None):
    return asyncio.run(_execute_ingestion(UUID(run_id), max_sessions=max_sessions))
async def _execute_ingestion(run_id: UUID, *, max_sessions: int | None = None):
    async with get_session_factory()() as db:
        run = await db.get(IngestionRunModel, run_id)
        if run is None:
            raise LookupError(f"Ingestion run {run_id} not found")
        connector_row = await db.get(ConnectorModel, run.connector_id)
        if connector_row is None:
            run.status = "failed"
            run.error_message = "Connector not found"
            await db.commit()
            raise LookupError("Connector not found")
        if not connector_row.enabled:
            run.status = "failed"
            run.error_message = "Connector is disabled"
            await db.commit()
            raise RuntimeError("Connector is disabled")
        connector = build_connector(connector_row)
        try:
            completed = await SnapshotIngestionService(db, connector).execute_existing_run(
                run_id, max_sessions=max_sessions
            )
            return {
                "run_id": str(completed.id),
                "status": completed.status,
                "session_count": completed.session_count,
                "activity_count": completed.activity_count,
            }
        finally:
            if isinstance(connector, QuartzRestConnector):
                await connector.close()
async def _ensure_chunks(db, scan):
    result = await db.execute(
        select(ScanChunkModel)
        .where(ScanChunkModel.scan_id == scan.id)
        .order_by(ScanChunkModel.chunk_index)
    )
    rows = list(result.scalars())
    if rows:
        return rows
    specs = split_date_range(scan.id, scan.date_from, scan.date_to, 1)
    rows = [
        ScanChunkModel(
            id=uuid4(),
            scan_id=scan.id,
            chunk_index=item.chunk_index,
            date_from=item.date_from,
            date_to=item.date_to,
            status="pending",
        )
        for item in specs
    ]
    db.add_all(rows)
    scan.total_chunks = len(rows)
    await db.commit()
    return rows
def _scan_response(scan):
    return {
        "scan_id": str(scan.id),
        "status": scan.status,
        "finalization_status": scan.finalization_status,
        "chunks": scan.total_chunks,
        "completed_chunks": scan.completed_chunks,
        "findings": scan.finding_count,
    }
def _lock_key(scan_id: UUID) -> int:
    # UUID-derived signed 64-bit advisory-lock namespace.
    value = int.from_bytes(scan_id.bytes[:8], "big", signed=False)
    return value - (1 << 64) if value >= (1 << 63) else value


async def _execute_scan(scan_id: UUID, worker_id: str):
    # Keep the lock on a dedicated physical connection, separate from
    # the session that commits each employee-day transaction.
    async with get_engine().connect() as lock_connection:
        key = _lock_key(scan_id)
        acquired = bool((await lock_connection.execute(
            text("SELECT pg_try_advisory_lock(:key)"), {"key": key}
        )).scalar_one())
        await lock_connection.commit()
        if not acquired:
            return {"scan_id": str(scan_id), "status": "already_running", "lock_acquired": False}
        owner_pid = (await lock_connection.execute(text("SELECT pg_backend_pid()"))).scalar_one()
        await lock_connection.commit()
        try:
            async with get_session_factory()() as db:
                scan = await db.get(AnalysisScanModel, scan_id)
                if scan is None:
                    raise LookupError("scan not found")
                if scan.status == "completed" and scan.finalization_status == "completed":
                    return _scan_response(scan)
                if scan.cancel_requested or scan.status == "cancelled":
                    scan.status = "cancelled"
                    await db.commit()
                    return _scan_response(scan)
                scan.status = ScanStatus.RUNNING.value
                scan.started_at = scan.started_at or datetime.now(timezone.utc)
                scan.engine_version = ENGINE_VERSION
                scan.rule_version = RULE_VERSION
                await db.commit()
                try:
                    chunks = await _ensure_chunks(db, scan)
                    for chunk in chunks:
                        await db.refresh(scan)
                        await db.refresh(chunk)
                        if scan.cancel_requested or scan.status == "cancelled":
                            scan.status = "cancelled"
                            await db.commit()
                            break
                        if chunk.status == "completed":
                            continue
                        checkpoint = dict(chunk.checkpoint_json or {})
                        # Only v2 checkpoints are atomic with their findings.
                        # Legacy checkpoints must replay safely, never skip work.
                        resume = checkpoint if checkpoint.get("version") == 2 else {}
                        last = (str(resume.get("last_shift_date", "")), str(resume.get("last_agent_id", "")))
                        processed = int(resume.get("processed", 0))
                        chunk.status = "running"
                        chunk.attempt += 1
                        chunk.worker_id = worker_id
                        chunk.started_at = datetime.now(timezone.utc)
                        chunk.error_message = None
                        await db.commit()
                        try:
                            keys = (await db.execute(
                                select(SessionSnapshotModel.agent_id, SessionSnapshotModel.shift_date)
                                .where(
                                    SessionSnapshotModel.ingestion_run_id == scan.ingestion_run_id,
                                    SessionSnapshotModel.shift_date >= chunk.date_from,
                                    SessionSnapshotModel.shift_date <= chunk.date_to,
                                )
                                .distinct()
                                .order_by(SessionSnapshotModel.shift_date, SessionSnapshotModel.agent_id)
                            )).all()
                            # Do not trust a checkpoint that is outside this chunk.
                            if resume and last not in {(str(d), str(a)) for a, d in keys}:
                                raise RuntimeError("Checkpoint is not present in chunk input")
                            for agent, shift in keys:
                                if resume and (str(shift), str(agent)) <= last:
                                    continue
                                await db.refresh(scan)
                                if scan.cancel_requested:
                                    break
                                # Detect lost lock connection before any new writes.
                                pid = (await lock_connection.execute(text("SELECT pg_backend_pid()"))).scalar_one()
                                await lock_connection.commit()
                                if pid != owner_pid:
                                    raise RuntimeError("Scan advisory lock connection changed")
                                # process_employee_day performs no commits. The
                                # findings and checkpoint commit atomically.
                                await process_employee_day(
                                    db, scan_id=scan.id, ingestion_run_id=scan.ingestion_run_id,
                                    agent_id=agent, shift_date=shift,
                                )
                                processed += 1
                                chunk.checkpoint_json = {
                                    "version": 2,
                                    "last_agent_id": str(agent),
                                    "last_shift_date": str(shift),
                                    "processed": processed,
                                }
                                chunk.employee_days_processed = processed
                                await db.commit()
                            if scan.cancel_requested:
                                chunk.status = "cancelled"
                            else:
                                chunk.status = "completed"
                                chunk.completed_at = datetime.now(timezone.utc)
                            # Count actual rows, including replayed legacy findings.
                            chunk.findings_persisted = (await db.execute(
                                select(func.count()).select_from(DurableFindingModel).where(
                                    DurableFindingModel.scan_id == scan.id,
                                    DurableFindingModel.shift_date >= chunk.date_from,
                                    DurableFindingModel.shift_date <= chunk.date_to,
                                )
                            )).scalar_one()
                            await db.commit()
                        except Exception as exc:
                            await db.rollback()
                            chunk = await db.get(ScanChunkModel, chunk.id)
                            chunk.status = "failed"
                            chunk.error_message = str(exc)[:4000]
                            await db.commit()
                            raise
                    counts = (await db.execute(
                        select(ScanChunkModel.status, func.count())
                        .where(ScanChunkModel.scan_id == scan.id)
                        .group_by(ScanChunkModel.status)
                    )).all()
                    chunk_counts = dict(counts)
                    scan.completed_chunks = chunk_counts.get("completed", 0)
                    scan.failed_chunks = chunk_counts.get("failed", 0)
                    scan.employee_days_processed = (await db.execute(
                        select(func.coalesce(func.sum(ScanChunkModel.employee_days_processed), 0))
                        .where(ScanChunkModel.scan_id == scan.id)
                    )).scalar_one()
                    scan.finding_count = (await db.execute(
                        select(func.count()).select_from(DurableFindingModel)
                        .where(DurableFindingModel.scan_id == scan.id)
                    )).scalar_one()
                    if scan.cancel_requested or chunk_counts.get("cancelled", 0):
                        scan.status = "cancelled"
                    elif scan.failed_chunks:
                        scan.status = "failed"
                    elif (
                        scan.total_chunks > 0
                        and scan.completed_chunks == scan.total_chunks
                        and await scan_is_ready_for_finalization(db, scan.id)
                    ):
                        summary = await summarize_scan(db, scan)
                        scan.summary_json = summary.model_dump(mode="json")
                        scan.finding_count = summary.total_findings
                        scan.finalization_status = "completed"
                        scan.status = "completed"
                        scan.completed_at = datetime.now(timezone.utc)
                        scan.error_message = None
                    else:
                        scan.status = "failed"
                        scan.error_message = "Scan finalization blocked: not all expected chunks completed"
                    await db.commit()
                    return _scan_response(scan)
                except Exception as exc:
                    await db.rollback()
                    scan = await db.get(AnalysisScanModel, scan_id)
                    if scan is not None and not (
                        scan.status == "completed" and scan.finalization_status == "completed"
                    ):
                        scan.status = "cancelled" if scan.cancel_requested else "failed"
                        scan.error_message = str(exc)[:4000]
                        await db.commit()
                    raise
        finally:
            try:
                released = (await lock_connection.execute(
                    text("SELECT pg_advisory_unlock(:key)"), {"key": key}
                )).scalar_one()
                await lock_connection.commit()
                if not released:
                    await lock_connection.invalidate()
                    raise RuntimeError("Scan advisory lock was not held at release")
            except Exception:
                await lock_connection.invalidate()
                raise
