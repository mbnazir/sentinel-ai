from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta
from hashlib import sha256
import json
from fastapi import logger
import structlog
from typing import TypeVar
from uuid import UUID, uuid4, uuid5

from sqlalchemy import func, select, tuple_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.connector_contract import WorkforceConnector
from app.application.normalized import (
    NormalizedActivity,
    NormalizedLoginSession,
)
from app.application.snapshot_hash import canonical_hash
from app.infrastructure.models import (
    ActivitySnapshotModel,
    IngestionActivityBatchModel,
    IngestionProgressModel,
    IngestionRunModel,
    SessionSnapshotModel,
)

SESSION_BATCH_SIZE = 200
ACTIVITY_BATCH_SIZE = 1000
LEASE_SECONDS = 600

T = TypeVar("T")


class IngestionRangeError(ValueError):
    pass


class IngestionAlreadyRunning(RuntimeError):
    pass


class IngestionConflictError(RuntimeError):
    pass


class LegacyRecoveryRequired(RuntimeError):
    pass


class SafeIngestionFailure(RuntimeError):
    def __init__(self, category: str, message: str) -> None:
        super().__init__(message)
        self.failure_category = category


def _safe_failure(exc: Exception) -> tuple[str, str]:
    category = getattr(exc, "failure_category", None) or type(exc).__name__.lower()
    if isinstance(exc, SafeIngestionFailure):
        return category, str(exc)[:500]
    if hasattr(exc, "http_status"):
        return category, f"Quartz request failed ({category})"
    if isinstance(exc, IngestionConflictError):
        return "snapshot_conflict", "Source snapshot changed within this ingestion run"
    return category[:80], f"Ingestion failed ({type(exc).__name__})"


def _model_values(model) -> dict[str, object]:
    """
    Convert a snapshot model into a consistent INSERT dictionary.

    Preserve explicit NULL values for nullable columns so that
    PostgreSQL multi-row INSERT statements have consistent keys.

    Omit uninitialized primary keys and database-generated columns.
    """
    values = {}

    for column in model.__table__.columns:
        key = column.key
        value = getattr(model, key, None)

        if value is not None:
            values[key] = value
        elif column.nullable:
            values[key] = None

    return values


class SnapshotIngestionService:
    """
    Pull normalized workforce data from a read-only connector and persist
    immutable Sentinel operational snapshots.

    The connector is responsible for translating source-system-specific
    formats into NormalizedLoginSession and NormalizedActivity.

    Sentinel persists those normalized records without modifying the source
    evidence.
    """
    async def execute_existing_run(
        self,
        run_id: UUID,
        *,
        max_sessions: int | None = None,
    ) -> IngestionRunModel:
        run = await self.db.get(IngestionRunModel, run_id)
        if run is None:
            raise LookupError("Ingestion run not found")
        existing_progress = await self.db.get(IngestionProgressModel, run_id)
        if existing_progress is None and run.status in {"failed", "partial"}:
            raise LegacyRecoveryRequired("Legacy run requires explicit recovery initialization")
        progress = await self._get_or_create_progress(run_id)
        if run.status == "completed":
            return run
        lease_token = await self._claim_run(run_id)
        logger = structlog.get_logger(__name__)
        run.status = "running"
        run.error_message = None
        run.completed_at = None
        progress.last_failure_category = None
        await self.db.commit()
        bounded_stop = False
        try:
            if hasattr(self.connector, "fetch_sessions_page"):
                bounded_stop = await self._collect_sessions(run, lease_token, max_sessions)
                await self._ensure_activity_batches(run_id)
                await self._process_activity_batches(run_id, lease_token)
                await self._update_reconciliation(run_id)
            else:
                # Preserve non-Quartz connector compatibility; this adapter is intentionally
                # marked unreconciled because iterator-only connectors have no durable cursor.
                await self._run_legacy_iterator(run, max_sessions)
                progress = await self.db.get(IngestionProgressModel, run_id)
                progress.session_collection_complete = True
                progress.completion_status = "UNVERIFIED"
                progress.reconciliation_status = "UNVERIFIED"
                progress.reconciliation_json = {"reason": "Connector does not expose page checkpoints"}
            current = await self.db.get(IngestionRunModel, run_id)
            progress = await self.db.get(IngestionProgressModel, run_id)
            counts = await self._persisted_counts(run_id)
            current.session_count = counts[0]
            current.activity_count = counts[1]
            current.completed_at = datetime.now(UTC)
            if bounded_stop:
                current.status = "partial"
                progress.completion_status = "PARTIAL"
            else:
                current.status = "completed"
                current.error_message = None
                if progress.completion_status not in {"COMPLETE", "UNVERIFIED"}:
                    progress.completion_status = "INCOMPLETE"
            progress.lease_token = None
            progress.lease_expires_at = None
            await self.db.commit()
            await self.db.refresh(current)
            logger.info("ingestion_run_checkpointed", ingestion_run_id=str(run_id),
                        completion_status=progress.completion_status,
                        reconciliation_status=progress.reconciliation_status,
                        session_count=counts[0], activity_count=counts[1])
            return current
        except Exception as exc:
            await self.db.rollback()
            safe_message, category = _safe_failure(exc)
            failed = await self.db.get(IngestionRunModel, run_id)
            progress = await self.db.get(IngestionProgressModel, run_id)
            if failed is not None:
                failed.status = "failed"
                failed.error_message = safe_message
                failed.completed_at = datetime.now(UTC)
                counts = await self._persisted_counts(run_id)
                failed.session_count, failed.activity_count = counts
            if progress is not None:
                progress.completion_status = "INCOMPLETE"
                progress.last_failure_category = category
                progress.lease_token = None
                progress.lease_expires_at = None
                await self.db.commit()
            logger.error("ingestion_run_failed", ingestion_run_id=str(run_id),
                         failure_category=category, error_type=type(exc).__name__)
            raise
    
    
    def __init__(
        self,
        db: AsyncSession,
        connector: WorkforceConnector,
    ) -> None:
        self.db = db
        self.connector = connector

    async def ingest(
        self,
        *,
        connector_id: UUID,
        shift_date_from: date,
        shift_date_to: date,
        idempotency_key: str,
        max_sessions: int | None = None,
    ) -> IngestionRunModel:
        self._validate_range(
            shift_date_from,
            shift_date_to,
        )

        existing = await self._find_existing(connector_id, idempotency_key)

        if existing is not None:
            return existing

        run = IngestionRunModel(
            connector_id=connector_id,
            idempotency_key=idempotency_key,
            shift_date_from=shift_date_from,
            shift_date_to=shift_date_to,
            status="queued",
        )

        self.db.add(run)

        await self.db.commit()
        await self.db.refresh(run)

        return await self.execute_existing_run(run.id, max_sessions=max_sessions)

    async def _get_or_create_progress(self, run_id: UUID) -> IngestionProgressModel:
        progress = await self.db.get(IngestionProgressModel, run_id)
        if progress is not None:
            return progress
        self.db.add(IngestionProgressModel(ingestion_run_id=run_id))
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
        progress = await self.db.get(IngestionProgressModel, run_id)
        if progress is None:
            raise RuntimeError("Could not initialize ingestion progress")
        return progress

    async def _claim_run(self, run_id: UUID) -> UUID:
        now = datetime.now(UTC)
        progress = await self.db.scalar(select(IngestionProgressModel)
            .where(IngestionProgressModel.ingestion_run_id == run_id).with_for_update())
        if progress is None:
            raise RuntimeError("Ingestion progress is missing")
        if progress.lease_expires_at and progress.lease_expires_at > now:
            raise IngestionAlreadyRunning("An ingestion worker already holds the run lease")
        token = uuid4()
        progress.lease_token = token
        progress.lease_expires_at = now + timedelta(seconds=LEASE_SECONDS)
        progress.completion_status = "RUNNING"
        await self.db.commit()
        return token

    async def _renew_lease(self, run_id: UUID, token: UUID) -> IngestionProgressModel:
        progress = await self.db.get(IngestionProgressModel, run_id)
        if progress is None or progress.lease_token != token:
            raise IngestionAlreadyRunning("Ingestion run lease was lost")
        progress.lease_expires_at = datetime.now(UTC) + timedelta(seconds=LEASE_SECONDS)
        return progress

    async def _collect_sessions(self, run: IngestionRunModel, lease_token: UUID,
                                max_sessions: int | None) -> bool:
        logger = structlog.get_logger(__name__)
        run_id = run.id
        while True:
            progress = await self.db.get(IngestionProgressModel, run_id)
            if progress.session_collection_complete:
                return False
            cursor = progress.session_cursor
            page_number = progress.session_page + 1
            page = await self.connector.fetch_sessions_page(
                shift_date_from=run.shift_date_from, shift_date_to=run.shift_date_to,
                cursor=cursor, context={"ingestion_run_id": str(run_id), "page_number": page_number})
            self._validate_session_batch(page.items, run.shift_date_from, run.shift_date_to)
            allowed = page.items
            truncated = False
            if max_sessions is not None:
                remaining = max_sessions - progress.sessions_persisted_count
                allowed = page.items[:max(0, remaining)]
                truncated = len(allowed) < len(page.items)
            new_cursor = page.next_cursor
            if new_cursor is not None and (new_cursor == cursor or new_cursor in (progress.session_seen_cursors_json or [])):
                raise SafeIngestionFailure("session_pagination_cursor_repeated", "Repeated session pagination cursor")
            if page.expected_count is not None:
                if progress.expected_session_count is not None and progress.expected_session_count != page.expected_count:
                    progress.source_count_mismatches_json = list(progress.source_count_mismatches_json or []) + [
                        "Quartz expected session count changed between pages"]
                progress.expected_session_count = page.expected_count
            await self._insert_session_rows(run_id, allowed)
            count = await self._count_sessions(run_id)
            progress.sessions_retrieved_count = count
            progress.sessions_persisted_count = count
            progress.session_page = page_number
            progress.session_seen_cursors_json = list(progress.session_seen_cursors_json or [])
            if new_cursor is not None and not truncated:
                progress.session_seen_cursors_json.append(new_cursor)
            progress.session_cursor = cursor if truncated else new_cursor
            progress.session_collection_complete = new_cursor is None and not truncated
            progress.last_successful_checkpoint_at = datetime.now(UTC)
            await self._renew_lease(run_id, lease_token)
            run.session_count = count
            await self.db.commit()
            logger.info("ingestion_session_page_checkpointed", ingestion_run_id=str(run_id),
                page_number=page_number, session_count=len(allowed), persisted_session_count=count,
                request_latency_ms=round(page.latency_ms, 2), retry_count=page.attempts - 1,
                session_collection_complete=progress.session_collection_complete)
            if truncated or (max_sessions is not None and count >= max_sessions
                             and not progress.session_collection_complete):
                return True
            if progress.session_collection_complete:
                return False

    async def _insert_session_rows(self, run_id: UUID, sessions: list[NormalizedLoginSession]) -> None:
        if not sessions:
            return
        rows = [_session_row(run_id, item) for item in sessions]
        values = [_model_values(row) for row in rows]
        stmt = pg_insert(SessionSnapshotModel).values(values).on_conflict_do_nothing(
            index_elements=["ingestion_run_id", "source_system", "source_session_id"])
        await self.db.execute(stmt)
        ids = [(row.source_system, row.source_session_id) for row in rows]
        for source_system in {key[0] for key in ids}:
            source_ids = [key[1] for key in ids if key[0] == source_system]
            result = await self.db.execute(select(SessionSnapshotModel.source_session_id,
                SessionSnapshotModel.content_hash).where(SessionSnapshotModel.ingestion_run_id == run_id,
                SessionSnapshotModel.source_system == source_system,
                SessionSnapshotModel.source_session_id.in_(source_ids)))
            hashes = {source_id: content_hash for source_id, content_hash in result.all()}
            for row in rows:
                if row.source_system == source_system and hashes.get(row.source_session_id) != row.content_hash:
                    logger = structlog.get_logger(__name__)

                    logger.error(
                        "ingestion_session_hash_conflict",
                        ingestion_run_id=str(run_id),
                        source_system=row.source_system,
                        source_session_id=row.source_session_id,
                        stored_content_hash=hashes.get(row.source_session_id),
                        incoming_content_hash=row.content_hash,
                    )
                    raise IngestionConflictError("Quartz session snapshot changed within an existing run")

    async def _insert_activity_rows(self, run_id: UUID, activities: list[NormalizedActivity]) -> None:
        if not activities:
            return
        rows = [_activity_row(run_id, item) for item in activities]
        await self.db.execute(pg_insert(ActivitySnapshotModel).values(
            [_model_values(row) for row in rows]).on_conflict_do_nothing(
                index_elements=["ingestion_run_id", "source_system", "source_session_id",
                                "source_activity_id", "data_source_id"]))
        identities = list({(row.source_system, row.source_session_id,
                            row.source_activity_id, row.data_source_id) for row in rows})
        result = await self.db.execute(select(
            ActivitySnapshotModel.source_system,
            ActivitySnapshotModel.source_session_id,
            ActivitySnapshotModel.source_activity_id,
            ActivitySnapshotModel.data_source_id,
            ActivitySnapshotModel.content_hash,
        ).where(
            ActivitySnapshotModel.ingestion_run_id == run_id,
            tuple_(ActivitySnapshotModel.source_system,
                   ActivitySnapshotModel.source_session_id,
                   ActivitySnapshotModel.source_activity_id,
                   ActivitySnapshotModel.data_source_id).in_(identities),
        ))
        hashes = {(source_system, session_id, activity_id, data_source_id): content_hash
                  for source_system, session_id, activity_id, data_source_id, content_hash in result.all()}
        for row in rows:
            identity = (row.source_system, row.source_session_id,
                        row.source_activity_id, row.data_source_id)
            if hashes.get(identity) != row.content_hash:
                raise IngestionConflictError("Quartz activity snapshot changed within an existing run")

    async def _count_sessions(self, run_id: UUID) -> int:
        return int(await self.db.scalar(select(func.count()).select_from(SessionSnapshotModel)
                                        .where(SessionSnapshotModel.ingestion_run_id == run_id)) or 0)

    async def _persisted_counts(self, run_id: UUID) -> tuple[int, int]:
        sessions = await self._count_sessions(run_id)
        activities = int(await self.db.scalar(select(func.count()).select_from(ActivitySnapshotModel)
                                              .where(ActivitySnapshotModel.ingestion_run_id == run_id)) or 0)
        return sessions, activities

    async def _ensure_activity_batches(self, run_id: UUID) -> None:
        result = await self.db.execute(select(SessionSnapshotModel.source_session_id)
            .where(SessionSnapshotModel.ingestion_run_id == run_id,
                   SessionSnapshotModel.source_system == "quartz")
            .order_by(SessionSnapshotModel.source_session_id))
        session_ids = [row[0] for row in result.all()]
        existing_result = await self.db.execute(select(IngestionActivityBatchModel.batch_key)
            .where(IngestionActivityBatchModel.ingestion_run_id == run_id))
        existing = {row[0] for row in existing_result.all()}
        batch_size = getattr(self.connector, "activity_session_id_batch_size", 25)
        for start in range(0, len(session_ids), batch_size):
            batch_sessions = session_ids[start:start + batch_size]
            key = sha256(json.dumps(batch_sessions, separators=(",", ":")).encode()).hexdigest()
            if key in existing:
                continue
            self.db.add(IngestionActivityBatchModel(id=uuid5(run_id, key), ingestion_run_id=run_id,
                batch_key=key, session_ids_json=batch_sessions, status="pending"))
        await self.db.commit()

    async def _process_activity_batches(self, run_id: UUID, lease_token: UUID) -> None:
        logger = structlog.get_logger(__name__)
        batch_result = await self.db.execute(select(IngestionActivityBatchModel.id)
            .where(IngestionActivityBatchModel.ingestion_run_id == run_id,
                   IngestionActivityBatchModel.status != "completed")
            .order_by(IngestionActivityBatchModel.batch_key))
        # Keep immutable scalar identities across commits/rollbacks. ORM rows
        # expire on rollback (and may expire on commit in alternate session
        # factories), so reading batch.id from them in an exception path can
        # trigger unsupported implicit async IO / MissingGreenlet.
        batch_ids = list(batch_result.scalars())
        for batch_id in batch_ids:
            batch = await self.db.get(IngestionActivityBatchModel, batch_id)
            batch.status = "running"
            batch.attempt_count += 1
            batch.last_failure_category = None
            batch.failure_code = None
            batch.safe_error_message = None
            await self._renew_lease(run_id, lease_token)
            await self.db.commit()
            attempted_page_number: int | None = None
            attempted_next_cursor: str | None = None
            try:
                while True:
                    batch = await self.db.get(IngestionActivityBatchModel, batch_id)
                    page_number = batch.page_number + 1
                    attempted_page_number = None
                    attempted_next_cursor = None
                    page = await self.connector.fetch_activities_page(
                        login_session_ids=list(batch.session_ids_json), cursor=batch.cursor,
                        context={"ingestion_run_id": str(run_id), "batch_id": str(batch_id),
                                 "session_id_count": len(batch.session_ids_json),
                                 "page_number": page_number})
                    self._validate_activity_batch(page.items, set(batch.session_ids_json))
                    next_cursor = page.next_cursor
                    if next_cursor is not None and (next_cursor == batch.cursor
                            or next_cursor in (batch.seen_cursors_json or [])):
                        raise SafeIngestionFailure("activity_pagination_cursor_repeated",
                                                   "Repeated activity pagination cursor")
                    if page.expected_count is not None:
                        if (batch.expected_activity_count is not None
                                and batch.expected_activity_count != page.expected_count):
                            batch.last_failure_category = "expected_count_changed"
                        batch.expected_activity_count = page.expected_count
                    await self._insert_activity_rows(run_id, page.items)
                    batch.activities_retrieved_count += len(page.items)
                    batch.page_number = page_number
                    batch.seen_cursors_json = list(batch.seen_cursors_json or [])
                    if next_cursor is not None:
                        batch.seen_cursors_json.append(next_cursor)
                    batch.cursor = next_cursor
                    batch.last_successful_checkpoint_at = datetime.now(UTC)
                    batch.status = "completed" if next_cursor is None else "running"
                    batch.completed_at = datetime.now(UTC) if next_cursor is None else None
                    result = await self.db.execute(select(func.count()).select_from(ActivitySnapshotModel)
                        .where(ActivitySnapshotModel.ingestion_run_id == run_id,
                               ActivitySnapshotModel.source_system == "quartz",
                               ActivitySnapshotModel.source_session_id.in_(batch.session_ids_json)))
                    batch.activities_persisted_count = int(result.scalar_one())
                    session_id_count = len(batch.session_ids_json)
                    checkpoint_status = batch.status
                    await self._renew_lease(run_id, lease_token)
                    # These scalar values let the handler distinguish a page
                    # transaction that rolled back from a commit whose server
                    # response was lost after PostgreSQL committed atomically.
                    attempted_page_number = page_number
                    attempted_next_cursor = next_cursor
                    await self.db.commit()
                    logger.info("ingestion_activity_page_checkpointed", ingestion_run_id=str(run_id),
                        batch_id=str(batch_id), session_id_count=session_id_count,
                        page_number=page_number, activity_count=len(page.items),
                        request_latency_ms=round(page.latency_ms, 2), retry_count=page.attempts - 1,
                        checkpoint_status=checkpoint_status)
                    if next_cursor is None:
                        break
            except Exception as exc:
                # Roll back first. The page rows and its checkpoint are one
                # transaction, so after rollback/reload we can safely decide
                # whether this page advanced durably without lazy-loading the
                # expired ORM object from the failed transaction.
                await self.db.rollback()
                batch = await self.db.get(IngestionActivityBatchModel, batch_id)
                page_committed = (
                    attempted_page_number is not None
                    and batch.page_number == attempted_page_number
                    and batch.cursor == attempted_next_cursor
                )
                if page_committed:
                    logger.warning("ingestion_activity_page_commit_confirmed_after_error",
                        ingestion_run_id=str(run_id), batch_id=str(batch_id),
                        page_number=attempted_page_number)
                    raise
                category, message = _safe_failure(exc)
                batch.status = "failed"
                batch.last_failure_category = category
                batch.failure_code = getattr(exc, "http_status", None)
                batch.safe_error_message = message
                await self.db.commit()
                raise

    async def _update_reconciliation(self, run_id: UUID) -> None:
        progress = await self.db.get(IngestionProgressModel, run_id)
        run = await self.db.get(IngestionRunModel, run_id)
        batches_result = await self.db.execute(select(IngestionActivityBatchModel)
            .where(IngestionActivityBatchModel.ingestion_run_id == run_id))
        batches = list(batches_result.scalars())
        persisted_sessions, persisted_activities = await self._persisted_counts(run_id)
        mismatches = list(progress.source_count_mismatches_json or [])
        if progress.expected_session_count is not None and progress.expected_session_count != persisted_sessions:
            mismatches.append("Quartz expected session count does not match persisted unique sessions")
        all_activity_counts_present = all(batch.expected_activity_count is not None for batch in batches)
        if all_activity_counts_present:
            expected_activity_total = sum(batch.expected_activity_count or 0 for batch in batches)
            if expected_activity_total != persisted_activities:
                mismatches.append("Quartz expected activity count does not match persisted unique activities")
            progress.expected_activity_count = expected_activity_total
        else:
            progress.expected_activity_count = None
        if not batches:
            progress.expected_activity_count = 0 if progress.expected_session_count == 0 else None
            all_activity_counts_present = progress.expected_activity_count is not None
        failed_batches = sum(batch.status != "completed" for batch in batches)
        progress.failed_activity_batches = sum(batch.status == "failed" for batch in batches)
        progress.sessions_with_completed_activities = sum(
            len(batch.session_ids_json) for batch in batches if batch.status == "completed")
        progress.activities_retrieved_count = sum(batch.activities_retrieved_count for batch in batches)
        progress.activities_persisted_count = persisted_activities
        coverage_result = await self.db.execute(select(SessionSnapshotModel.shift_date, func.count())
            .where(SessionSnapshotModel.ingestion_run_id == run_id)
            .group_by(SessionSnapshotModel.shift_date).order_by(SessionSnapshotModel.shift_date))
        observed_dates = {row[0].isoformat(): row[1] for row in coverage_result.all()}
        requested_dates = [date.fromordinal(run.shift_date_from.toordinal() + offset).isoformat()
                           for offset in range((run.shift_date_to - run.shift_date_from).days + 1)]
        progress.date_coverage_json = {"requested_dates": requested_dates,
            "observed_session_counts": observed_dates,
            "dates_without_sessions": [day for day in requested_dates if day not in observed_dates],
            "source_date_counts_reconciled": False}
        retrieval_complete = progress.session_collection_complete and failed_batches == 0
        if not retrieval_complete:
            progress.reconciliation_status = "INCOMPLETE"
            progress.completion_status = "INCOMPLETE"
        elif mismatches:
            progress.reconciliation_status = "MISMATCH"
            progress.completion_status = "INCOMPLETE"
        elif progress.expected_session_count is None or not all_activity_counts_present:
            progress.reconciliation_status = "UNVERIFIED"
            progress.completion_status = "UNVERIFIED"
        else:
            progress.reconciliation_status = "RECONCILED"
            progress.completion_status = "COMPLETE"
        progress.source_count_mismatches_json = list(dict.fromkeys(mismatches))
        progress.reconciliation_json = {"retrieval_complete": retrieval_complete,
            "expected_counts_available": progress.expected_session_count is not None and all_activity_counts_present,
            "sessions_match": progress.expected_session_count == persisted_sessions
                if progress.expected_session_count is not None else None,
            "all_activity_batches_complete": failed_batches == 0,
            "activity_batch_count": len(batches), "failed_activity_batch_count": progress.failed_activity_batches,
            "persisted_unique_session_count": persisted_sessions,
            "persisted_unique_activity_count": persisted_activities,
            "mismatches": progress.source_count_mismatches_json}
        await self.db.commit()

    async def _run_legacy_iterator(self, run: IngestionRunModel, max_sessions: int | None) -> None:
        session_stream = self.connector.iter_sessions(shift_date_from=run.shift_date_from,
                                                      shift_date_to=run.shift_date_to)
        if max_sessions is not None:
            session_stream = _take(session_stream, max_sessions)
        async for sessions in _batched(session_stream, SESSION_BATCH_SIZE):
            self._validate_session_batch(sessions, run.shift_date_from, run.shift_date_to)
            await self._persist_sessions(run.id, sessions)
            ids = [session.source_session_id for session in sessions]
            async for activities in _batched(self.connector.iter_activities(login_session_ids=ids), ACTIVITY_BATCH_SIZE):
                self._validate_activity_batch(activities, set(ids))
                await self._persist_activities(run.id, activities)
        run.session_count, run.activity_count = await self._persisted_counts(run.id)
        await self.db.commit()

    async def _find_existing(
        self,
        connector_id: UUID,
        idempotency_key: str,
    ) -> IngestionRunModel | None:
        return await self.db.scalar(
            select(IngestionRunModel).where(
                IngestionRunModel.connector_id == connector_id,
                IngestionRunModel.idempotency_key == idempotency_key,
            )
        )

    async def _persist_sessions(
        self,
        run_id: UUID,
        sessions: list[NormalizedLoginSession],
    ) -> None:
        if not sessions:
            return

        rows = [
            _session_row(
                run_id,
                session,
            )
            for session in sessions
        ]

        self.db.add_all(rows)

        await self.db.commit()

    async def _persist_activities(
        self,
        run_id: UUID,
        activities: list[NormalizedActivity],
    ) -> None:
        if not activities:
            return

        rows = [
            _activity_row(
                run_id,
                activity,
            )
            for activity in activities
        ]

        self.db.add_all(rows)

        await self.db.commit()

    @staticmethod
    def _validate_range(
        shift_date_from: date,
        shift_date_to: date,
    ) -> None:
        if shift_date_to < shift_date_from:
            raise IngestionRangeError(
                "shift_date_to must not be before shift_date_from"
            )

        if (shift_date_to - shift_date_from).days > 31:
            raise IngestionRangeError(
                "a single ingestion run cannot exceed 32 shift dates"
            )

    @staticmethod
    def _validate_session_batch(
        sessions: list[NormalizedLoginSession],
        shift_date_from: date,
        shift_date_to: date,
    ) -> None:
        ids: set[str] = set()

        for session in sessions:
            if session.source_session_id in ids:
                raise ValueError(
                    "duplicate source session id " f"{session.source_session_id}"
                )

            ids.add(session.source_session_id)

            if not (shift_date_from <= session.shift_date <= shift_date_to):
                raise ValueError(
                    "connector returned session outside requested "
                    "shift-date range: "
                    f"{session.source_session_id}, "
                    f"shift_date={session.shift_date}"
                )

            if session.end_at is not None and session.end_at < session.start_at:
                raise ValueError(
                    f"session {session.source_session_id} " "has end_at before start_at"
                )

    @staticmethod
    def _validate_activity_batch(
        activities: list[NormalizedActivity],
        expected_session_ids: set[str],
    ) -> None:
        ids: set[str] = set()

        for activity in activities:
            if activity.source_activity_id in ids:
                raise ValueError(
                    "duplicate source activity id " f"{activity.source_activity_id}"
                )

            ids.add(activity.source_activity_id)

            if activity.source_session_id not in expected_session_ids:
                raise ValueError(
                    f"activity {activity.source_activity_id} "
                    "references unexpected login session "
                    f"{activity.source_session_id}"
                )

            if activity.end_at is not None and activity.end_at < activity.start_at:
                raise ValueError(
                    f"activity {activity.source_activity_id} "
                    "has end_at before start_at"
                )

            if activity.duration_seconds is not None and activity.duration_seconds < 0:
                raise ValueError(
                    f"activity {activity.source_activity_id} "
                    "has negative duration_seconds"
                )

            if activity.inactivity_seconds < 0:
                raise ValueError(
                    f"activity {activity.source_activity_id} "
                    "has negative inactivity_seconds"
                )

async def _take(
    stream: AsyncIterator[T],
    limit: int,
) -> AsyncIterator[T]:
    count = 0

    async for item in stream:
        if count >= limit:
            break

        yield item
        count += 1

        if count >= limit:
            break
        
async def _batched(
    stream: AsyncIterator[T],
    size: int,
) -> AsyncIterator[list[T]]:
    """
    Consume an async iterator and yield lists containing at most `size`
    normalized records.
    """

    if size <= 0:
        raise ValueError("batch size must be greater than zero")

    batch: list[T] = []

    async for item in stream:
        batch.append(item)

        if len(batch) >= size:
            yield batch
            batch = []

    if batch:
        yield batch


def _session_row(
    run_id: UUID,
    item: NormalizedLoginSession,
) -> SessionSnapshotModel:
    """
    Map a normalized login session to Sentinel's immutable session snapshot.
    """

    content = item.model_dump(
        mode="json",
        exclude_none=False,
    )

    return SessionSnapshotModel(
        ingestion_run_id=run_id,
        source_system=item.source_system,
        source_session_id=item.source_session_id,
        agent_id=item.agent_id,
        supervisor_id=item.supervisor_id,
        manager_id=item.manager_id,
        site_id=item.site_id,
        site_name=item.site_name,
        team_id=item.team_id,
        shift_date=item.shift_date,
        start_at=item.start_at,
        end_at=item.end_at,
        status_id=item.status_id,
        dispute_reason_id=item.dispute_reason_id,
        dispute_state=item.dispute_state,
        supervisor_status_id=item.supervisor_status_id,
        ready_for_payroll=item.ready_for_payroll,
        payroll_adjusted=item.payroll_adjusted,
        payroll_adjusted_at=item.payroll_adjusted_at,
        session_added_by=item.session_added_by,
        add_session_reason_id=item.add_session_reason_id,
        agent_action_at=item.agent_action_at,
        supervisor_action_at=item.supervisor_action_at,
        manager_action_at=item.manager_action_at,
        multiple_logins=item.multiple_logins,
        agent_ip=item.agent_ip,
        machine_hostname=item.machine_hostname,
        primary_campaign_id=item.primary_campaign_id,
        primary_campaign_name=item.primary_campaign_name,
        primary_client_id=item.primary_client_id,
        primary_client_name=item.primary_client_name,
        content_hash=canonical_hash(content),
        metadata_json=item.metadata,
    )


def _activity_row(
    run_id: UUID,
    item: NormalizedActivity,
) -> ActivitySnapshotModel:
    """
    Map a normalized activity to Sentinel's immutable activity snapshot.
    """

    content = item.model_dump(
        mode="json",
        exclude_none=False,
    )

    return ActivitySnapshotModel(
        ingestion_run_id=run_id,
        source_system=item.source_system,
        source_activity_id=item.source_activity_id,
        source_session_id=item.source_session_id,
        agent_id=item.agent_id,
        data_source_id=item.data_source_id,
        activity_type_id=item.activity_type_id,
        source_id=item.source_id,
        start_at=item.start_at,
        end_at=item.end_at,
        duration_seconds=item.duration_seconds,
        inactivity_seconds=item.inactivity_seconds,
        campaign_id=item.campaign_id,
        campaign_name=item.campaign_name,
        client_id=item.client_id,
        comment=item.comment,
        source_created_at=item.created_at,
        source_updated_at=item.updated_at,
        content_hash=canonical_hash(content),
        metadata_json=item.metadata,
    )
