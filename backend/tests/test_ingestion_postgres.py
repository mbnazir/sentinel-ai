"""Opt-in PostgreSQL integration tests, isolated in a temporary schema.

Run with SENTINEL_TEST_DATABASE_URL pointing at a disposable database whose
name contains `_test`; these tests never connect to the application's default
database and never drop a database or PostgreSQL volume.
"""
from __future__ import annotations

import os
import asyncio
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.engine import make_url

from app.application.ingestion import (IngestionAlreadyRunning, IngestionConflictError,
                                       SnapshotIngestionService)
from app.application.normalized import NormalizedActivity, NormalizedLoginSession
from app.application.snapshot_hash import canonical_hash
from app.core.database import Base
from app.core.auth import Role, require_roles
from app.core.security import create_access_token
from app.api.v1.routes_ingestion import get_ingestion_progress, initialize_legacy_recovery, router
from app.infrastructure.models import (
    AnalysisScanModel,
    ActivitySnapshotModel,
    ConnectorModel,
    DurableFindingModel,
    IngestionActivityBatchModel,
    IngestionProgressModel,
    IngestionRunModel,
    InvestigationAuditEventModel,
    InvestigationCaseModel,
    SessionSnapshotModel,
)

pytestmark = [pytest.mark.postgres_integration, pytest.mark.asyncio]


@pytest.fixture
async def postgres_db():
    url = os.getenv("SENTINEL_TEST_DATABASE_URL")
    if not url:
        pytest.skip("SENTINEL_TEST_DATABASE_URL is not set")
    parsed = make_url(url)
    if "_test" not in (parsed.database or "").lower():
        pytest.fail("refusing integration tests unless database name contains '_test'")
    admin_engine = create_async_engine(url)
    schema = f"ingest_test_{uuid4().hex}"
    async with admin_engine.begin() as connection:
        await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_async_engine(url, connect_args={"server_settings": {"search_path": schema}})
    tables = [ConnectorModel.__table__, IngestionRunModel.__table__,
              SessionSnapshotModel.__table__, ActivitySnapshotModel.__table__,
              IngestionProgressModel.__table__, IngestionActivityBatchModel.__table__,
              AnalysisScanModel.__table__, DurableFindingModel.__table__,
              InvestigationCaseModel.__table__, InvestigationAuditEventModel.__table__]
    async with engine.begin() as connection:
        await connection.run_sync(lambda sync_connection: Base.metadata.create_all(
            sync_connection, tables=tables))
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()
        async with admin_engine.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        await admin_engine.dispose()


def _session(session_id: str = "ss-1") -> NormalizedLoginSession:
    return NormalizedLoginSession(source_system="quartz", source_session_id=session_id,
        agent_id="synthetic-agent", shift_date=date(2026, 8, 26),
        start_at=datetime(2026, 8, 26, 8, tzinfo=timezone.utc), end_at=None)


def _activity(activity_id: str = "a-1", *, comment: str = "original",
              data_source_id: int = 1) -> NormalizedActivity:
    return NormalizedActivity(source_system="quartz", source_activity_id=activity_id,
        source_session_id="ss-1", agent_id="synthetic-agent", data_source_id=data_source_id,
        activity_type_id=2, source_id=None, start_at=datetime(2026, 8, 26, 8, tzinfo=timezone.utc),
        end_at=datetime(2026, 8, 26, 8, 1, tzinfo=timezone.utc), duration_seconds=60,
        inactivity_seconds=0, campaign_id=None, campaign_name=None, client_id=None,
        comment=comment, created_at=None, updated_at=None, metadata={})


async def _seed_run(factory, *, status="failed"):
    async with factory() as db:
        connector = ConnectorModel(name="synthetic", connector_type="quartz", mode="rest-api",
                                   enabled=True, config_json={})
        db.add(connector)
        await db.flush()
        run = IngestionRunModel(connector_id=connector.id, idempotency_key=f"test-{uuid4()}",
            shift_date_from=date(2026, 8, 26), shift_date_to=date(2026, 8, 26), status=status,
            session_count=0, activity_count=0)
        db.add(run)
        await db.commit()
        return run.id


class PageConnector:
    activity_session_id_batch_size = 25

    def __init__(self, *, fail_after_first_activity_page=False, authoritative_counts=False,
                 activity_expected_count=None):
        self.fail_after_first_activity_page = fail_after_first_activity_page
        self.authoritative_counts = authoritative_counts
        self.activity_expected_count = activity_expected_count
        self.activity_calls = 0

    async def fetch_sessions_page(self, *, shift_date_from, shift_date_to, cursor, context):
        from app.connectors.quartz.rest import QuartzPageResult
        rows = [_session()] if cursor is None else []
        return QuartzPageResult(rows, None, 1 if self.authoritative_counts else None, 1, 1.0)

    async def fetch_activities_page(self, *, login_session_ids, cursor, context):
        from app.connectors.quartz.rest import QuartzPageResult
        self.activity_calls += 1
        if self.fail_after_first_activity_page and cursor == "page-2":
            raise RuntimeError("synthetic source interruption")
        if cursor is None and self.fail_after_first_activity_page:
            return QuartzPageResult([_activity("a-1")], "page-2", None, 1, 1.0)
        return QuartzPageResult([_activity("a-1")], None, self.activity_expected_count, 1, 1.0)


async def test_legacy_checkpoint_absence_and_unknown_run_are_distinct(postgres_db):
    run_id = await _seed_run(postgres_db)
    async with postgres_db() as db:
        assert await db.get(IngestionProgressModel, run_id) is None
        assert await db.get(IngestionRunModel, uuid4()) is None
        counts = await db.scalar(select(text("count(*)")).select_from(SessionSnapshotModel)
                                 .where(SessionSnapshotModel.ingestion_run_id == run_id))
        assert counts == 0


async def test_legacy_recovery_initialization_preserves_snapshots_and_is_idempotent(postgres_db):
    run_id = await _seed_run(postgres_db)
    principal = type("Actor", (), {"subject": "operator-7"})()
    async with postgres_db() as db:
        service = SnapshotIngestionService(db, PageConnector())
        await service._insert_session_rows(run_id, [_session()])
        await service._insert_activity_rows(run_id, [_activity()])
        await db.commit()
        before = (await db.scalar(select(text("count(*)")).select_from(SessionSnapshotModel)
                                   .where(SessionSnapshotModel.ingestion_run_id == run_id)),
                  await db.scalar(select(text("count(*)")).select_from(ActivitySnapshotModel)
                                  .where(ActivitySnapshotModel.ingestion_run_id == run_id)))
    async def initialize_once():
        async with postgres_db() as db:
            return await initialize_legacy_recovery(run_id, db, principal)
    first, second = await asyncio.gather(initialize_once(), initialize_once())
    assert first.checkpoint_availability == "AVAILABLE"
    assert first.recovery_attempt_count == second.recovery_attempt_count == 1
    async with postgres_db() as db:
        after = (await db.scalar(select(text("count(*)")).select_from(SessionSnapshotModel)
                                  .where(SessionSnapshotModel.ingestion_run_id == run_id)),
                 await db.scalar(select(text("count(*)")).select_from(ActivitySnapshotModel)
                                 .where(ActivitySnapshotModel.ingestion_run_id == run_id)))
        progress = await db.get(IngestionProgressModel, run_id)
        assert progress.session_collection_complete is False
        assert progress.reconciliation_status == "INCOMPLETE"
        assert progress.recovery_initialized_by == "operator-7"
    assert after == before == (1, 1)


async def test_expired_lease_can_be_taken_over_but_active_lease_is_rejected(postgres_db):
    run_id = await _seed_run(postgres_db)
    async with postgres_db() as db:
        progress = IngestionProgressModel(ingestion_run_id=run_id,
            lease_token=uuid4(), lease_expires_at=datetime.now(timezone.utc) + timedelta(minutes=2))
        db.add(progress)
        await db.commit()
        service = SnapshotIngestionService(db, PageConnector())
        with pytest.raises(IngestionAlreadyRunning):
            await service._claim_run(run_id)
        progress.lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        await db.commit()
        token = await service._claim_run(run_id)
        assert token == progress.lease_token


async def test_activity_checkpoint_commits_with_page_and_replay_is_idempotent(postgres_db):
    run_id = await _seed_run(postgres_db, status="queued")
    connector = PageConnector()
    async with postgres_db() as db:
        run = await db.get(IngestionRunModel, run_id)
        result = await SnapshotIngestionService(db, connector).execute_existing_run(run_id)
        assert result.status == "completed"
        progress = await db.get(IngestionProgressModel, run_id)
        batch = (await db.execute(select(IngestionActivityBatchModel).where(
            IngestionActivityBatchModel.ingestion_run_id == run_id))).scalar_one()
        assert batch.status == "completed"
        assert batch.page_number == 1
        assert progress.completion_status == "UNVERIFIED"
        assert await db.scalar(select(text("count(*)")).select_from(ActivitySnapshotModel)
                               .where(ActivitySnapshotModel.ingestion_run_id == run_id)) == 1
        await SnapshotIngestionService(db, connector)._insert_activity_rows(run_id, [_activity("a-1")])
        await db.commit()
        assert await db.scalar(select(text("count(*)")).select_from(ActivitySnapshotModel)
                               .where(ActivitySnapshotModel.ingestion_run_id == run_id)) == 1


async def test_activity_content_hash_conflict_is_explicit(postgres_db):
    run_id = await _seed_run(postgres_db)
    async with postgres_db() as db:
        service = SnapshotIngestionService(db, PageConnector())
        await service._insert_activity_rows(run_id, [_activity("same", comment="first")])
        await db.commit()
        with pytest.raises(IngestionConflictError):
            await service._insert_activity_rows(run_id, [_activity("same", comment="changed")])
        await db.rollback()


async def test_same_activity_id_at_distinct_quartz_revision_stages_is_preserved(postgres_db):
    run_id = await _seed_run(postgres_db)
    async with postgres_db() as db:
        service = SnapshotIngestionService(db, PageConnector())
        await service._insert_activity_rows(run_id, [
            _activity("shared-id", data_source_id=2),
            _activity("shared-id", comment="supervisor stage", data_source_id=3),
        ])
        await db.commit()
        result = await db.execute(select(ActivitySnapshotModel.data_source_id).where(
            ActivitySnapshotModel.ingestion_run_id == run_id).order_by(ActivitySnapshotModel.data_source_id))
        assert result.scalars().all() == [2, 3]


async def test_failure_before_activity_checkpoint_commit_rolls_back_page(postgres_db, monkeypatch):
    run_id = await _seed_run(postgres_db, status="queued")
    async with postgres_db() as db:
        service = SnapshotIngestionService(db, PageConnector())
        original_commit = db.commit
        calls = 0
        async def fail_activity_page_commit():
            nonlocal calls
            calls += 1
            # Progress creation, lease, run status, session page, batch creation,
            # and batch-running state commit before the activity-page transaction.
            if calls == 7:
                raise RuntimeError("synthetic crash before page/checkpoint commit")
            await original_commit()
        monkeypatch.setattr(db, "commit", fail_activity_page_commit)
        with pytest.raises(RuntimeError, match="synthetic crash"):
            await service.execute_existing_run(run_id)
        monkeypatch.setattr(db, "commit", original_commit)
        progress = await db.get(IngestionProgressModel, run_id)
        batch = (await db.execute(select(IngestionActivityBatchModel).where(
            IngestionActivityBatchModel.ingestion_run_id == run_id))).scalar_one()
        batch_id = batch.id
        count = await db.scalar(select(text("count(*)")).select_from(ActivitySnapshotModel)
                                .where(ActivitySnapshotModel.ingestion_run_id == run_id))
        assert count == 0
        assert batch.cursor is None
        assert batch.status == "failed"
        assert progress.completion_status == "INCOMPLETE"
        # Resume from the unadvanced cursor. The failed page inserts no row;
        # successful replay persists exactly one row and advances one page.
        result = await service.execute_existing_run(run_id)
        assert result.status == "completed"
        batch = await db.get(IngestionActivityBatchModel, batch_id)
        assert batch.status == "completed"
        assert batch.page_number == 1
        assert await db.scalar(select(text("count(*)")).select_from(ActivitySnapshotModel)
                               .where(ActivitySnapshotModel.ingestion_run_id == run_id)) == 1


async def test_progress_and_resume_endpoint_authorization(postgres_db, monkeypatch):
    run_id = await _seed_run(postgres_db)
    app = FastAPI()
    app.include_router(router, prefix="/api/v1", dependencies=[Depends(
        require_roles(Role.MANAGER, Role.ADMIN))])
    async def override_db():
        async with postgres_db() as db:
            yield db
    from app.core.database import get_db
    app.dependency_overrides[get_db] = override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.get(f"/api/v1/ingestion-runs/{run_id}/progress")).status_code == 401
        viewer = create_access_token("viewer", Role.VIEWER.value)
        assert (await client.get(f"/api/v1/ingestion-runs/{run_id}/progress",
            headers={"Authorization": f"Bearer {viewer}"})).status_code == 403
        manager = create_access_token("manager", Role.MANAGER.value)
        response = await client.get(f"/api/v1/ingestion-runs/{run_id}/progress",
            headers={"Authorization": f"Bearer {manager}"})
        assert response.status_code == 200
        result = response.json()
        assert result["checkpoint_availability"] == "LEGACY_MISSING"
        assert result["recovery_eligible"] is True
        assert "employee_id" not in result
        assert (await client.get(f"/api/v1/ingestion-runs/{uuid4()}/progress",
            headers={"Authorization": f"Bearer {manager}"})).status_code == 404
        assert (await client.post(f"/api/v1/ingestion-runs/{run_id}/resume",
            headers={"Authorization": f"Bearer {viewer}"})).status_code == 403
        monkeypatch.setattr("app.api.v1.routes_ingestion.execute_ingestion.delay",
                            lambda *args: None)
        initialized = await client.post(
            f"/api/v1/ingestion-runs/{run_id}/recovery-initialize",
            headers={"Authorization": f"Bearer {manager}"})
        assert initialized.status_code == 200
        assert initialized.json()["recovery_attempt_count"] == 1
        resumed = await client.post(f"/api/v1/ingestion-runs/{run_id}/resume",
            headers={"Authorization": f"Bearer {manager}"})
        assert resumed.status_code == 202


async def test_source_failure_leaves_run_incomplete_and_checkpointed_page_durable(postgres_db):
    run_id = await _seed_run(postgres_db, status="queued")
    async with postgres_db() as db:
        service = SnapshotIngestionService(db, PageConnector(fail_after_first_activity_page=True))
        with pytest.raises(RuntimeError, match="synthetic source interruption"):
            await service.execute_existing_run(run_id)
        progress = await db.get(IngestionProgressModel, run_id)
        batch = (await db.execute(select(IngestionActivityBatchModel).where(
            IngestionActivityBatchModel.ingestion_run_id == run_id))).scalar_one()
        assert progress.completion_status == "INCOMPLETE"
        assert batch.status == "failed"
        assert batch.cursor == "page-2"
        assert await db.scalar(select(text("count(*)")).select_from(ActivitySnapshotModel)
                               .where(ActivitySnapshotModel.ingestion_run_id == run_id)) == 1


async def test_authoritative_count_mismatch_blocks_reconciliation(postgres_db):
    run_id = await _seed_run(postgres_db, status="queued")
    async with postgres_db() as db:
        await SnapshotIngestionService(db, PageConnector(activity_expected_count=2)).execute_existing_run(run_id)
        progress = await db.get(IngestionProgressModel, run_id)
        assert progress.reconciliation_status == "MISMATCH"
        assert progress.completion_status == "INCOMPLETE"
        assert progress.source_count_mismatches_json


QF001_TRANSITIONS = {
    "180660384": (4, 5),
    "180667650": (5, 4),
    "180689901": (4, 5),
    "180690354": (4, 5),
    "180691869": (4, 5),
}


async def _seed_qf001_pair(
    factory,
    *,
    earlier_run_status="completed",
    earlier_completion="COMPLETE",
    earlier_reconciliation="RECONCILED",
    later_run_status="completed",
    later_completion="COMPLETE",
    later_reconciliation="RECONCILED",
):
    earlier_id = uuid4()
    later_id = uuid4()
    async with factory() as db:
        connector = ConnectorModel(name="qf-test", connector_type="quartz", mode="rest-api",
                                   enabled=True, config_json={})
        db.add(connector)
        await db.flush()
        for run_id, started_at, run_status, completion, reconciliation in (
            (earlier_id, datetime(2026, 8, 25, tzinfo=timezone.utc), earlier_run_status,
             earlier_completion, earlier_reconciliation),
            (later_id, datetime(2026, 8, 27, tzinfo=timezone.utc), later_run_status,
             later_completion, later_reconciliation),
        ):
            db.add(IngestionRunModel(
                id=run_id, connector_id=connector.id, idempotency_key=str(run_id),
                shift_date_from=date(2026, 8, 26), shift_date_to=date(2026, 8, 26),
                status=run_status, started_at=started_at, session_count=5, activity_count=0,
            ))
            db.add(IngestionProgressModel(
                ingestion_run_id=run_id, completion_status=completion,
                reconciliation_status=reconciliation, session_collection_complete=True,
                expected_session_count=5 if reconciliation == "RECONCILED" else None,
                sessions_persisted_count=5,
            ))
            for session_id, statuses in QF001_TRANSITIONS.items():
                supervisor_status_id = statuses[0] if run_id == earlier_id else statuses[1]
                observed_at = datetime(
                    2026, 8, 26, 18 if run_id == earlier_id else 19,
                    tzinfo=timezone.utc,
                )
                db.add(SessionSnapshotModel(
                    ingestion_run_id=run_id,
                    source_system="quartz",
                    source_session_id=session_id,
                    agent_id="synthetic-agent",
                    shift_date=date(2026, 8, 26),
                    start_at=datetime(2026, 8, 26, 8, tzinfo=timezone.utc),
                    end_at=datetime(2026, 8, 26, 16, tzinfo=timezone.utc),
                    status_id=2,
                    supervisor_status_id=supervisor_status_id,
                    ready_for_payroll=True,
                    manager_action_at=datetime(2026, 8, 26, 17, tzinfo=timezone.utc),
                    content_hash=canonical_hash(NormalizedLoginSession(
                        source_system="quartz",
                        source_session_id=session_id,
                        agent_id="synthetic-agent",
                        shift_date=date(2026, 8, 26),
                        start_at=datetime(2026, 8, 26, 8, tzinfo=timezone.utc),
                        end_at=datetime(2026, 8, 26, 16, tzinfo=timezone.utc),
                        status_id=2,
                        supervisor_status_id=supervisor_status_id,
                        ready_for_payroll=True,
                        manager_action_at=datetime(2026, 8, 26, 17, tzinfo=timezone.utc),
                        metadata={},
                    )),
                    metadata_json={},
                    observed_at=observed_at,
                ))
        await db.commit()
    return earlier_id, later_id


async def _qf001_scan(
    factory,
    earlier_id,
    later_id,
    *,
    eligibility_mode="STRICT_RECONCILED",
    override_reason=None,
    override_role=None,
):
    scan = AnalysisScanModel(
        id=uuid4(), ingestion_run_id=later_id, baseline_ingestion_run_id=earlier_id,
        date_from=date(2026, 8, 26), date_to=date(2026, 8, 26),
        requested_by="test-investigator", scope="historical_comparison", status="running",
        eligibility_mode=eligibility_mode,
        eligibility_override_reason=override_reason,
        eligibility_override_role=override_role,
    )
    async with factory() as db:
        db.add(scan)
        await db.commit()
    return scan.id


async def test_qf001_persists_expected_five_findings_and_both_run_provenance(postgres_db):
    from app.workers.pipeline import process_qf001_scan

    earlier_id, later_id = await _seed_qf001_pair(postgres_db)
    scan_id = await _qf001_scan(postgres_db, earlier_id, later_id)
    async with postgres_db() as db:
        scan = await db.get(AnalysisScanModel, scan_id)
        snapshots_before = set((await db.execute(select(
            SessionSnapshotModel.id, SessionSnapshotModel.content_hash
        ))).all())
        evaluated, inserted, _context = await process_qf001_scan(db, scan)
        await db.commit()
        rows = list((await db.execute(select(DurableFindingModel).where(
            DurableFindingModel.scan_id == scan_id))).scalars())
        assert (evaluated, inserted, len(rows)) == (5, 5, 5)
        assert {row.source_session_id for row in rows} == set(QF001_TRANSITIONS)
        assert all(row.rule_id == "QF-001" for row in rows)
        for row in rows:
            earlier = row.evidence_json["metadata"]["earlier"]
            later = row.evidence_json["metadata"]["later"]
            assert earlier["ingestion_run_id"] == str(earlier_id)
            assert later["ingestion_run_id"] == str(later_id)
            assert earlier["snapshot_id"] and later["snapshot_id"]
        snapshots_after = set((await db.execute(select(
            SessionSnapshotModel.id, SessionSnapshotModel.content_hash
        ))).all())
        assert snapshots_after == snapshots_before


async def test_qf001_scan_creation_requires_explicit_chronological_baseline(postgres_db):
    from app.investigations.models import ScanCreate
    from app.investigations.service import create_scan

    earlier_id, later_id = await _seed_qf001_pair(postgres_db)
    async with postgres_db() as db:
        with pytest.raises(ValueError, match="requires baseline"):
            await create_scan(db, ScanCreate(
                ingestion_run_id=later_id, date_from=date(2026, 8, 26),
                date_to=date(2026, 8, 26), requested_by="tester",
                scope="historical_comparison",
            ))
        with pytest.raises(ValueError, match="distinct"):
            await create_scan(db, ScanCreate(
                ingestion_run_id=later_id, baseline_ingestion_run_id=later_id,
                date_from=date(2026, 8, 26), date_to=date(2026, 8, 26),
                requested_by="tester", scope="historical_comparison",
            ))
        with pytest.raises(ValueError, match="chronologically later"):
            await create_scan(db, ScanCreate(
                ingestion_run_id=earlier_id, baseline_ingestion_run_id=later_id,
                date_from=date(2026, 8, 26), date_to=date(2026, 8, 26),
                requested_by="tester", scope="historical_comparison",
            ))


async def test_qf001_repeat_and_cross_scan_replay_deduplicate_without_changing_hashes(postgres_db):
    from app.workers.pipeline import process_qf001_scan

    earlier_id, later_id = await _seed_qf001_pair(postgres_db)
    first_scan_id = await _qf001_scan(postgres_db, earlier_id, later_id)
    async with postgres_db() as db:
        scan = await db.get(AnalysisScanModel, first_scan_id)
        assert (await process_qf001_scan(db, scan))[:2] == (5, 5)
        await db.commit()
        before = dict((row.finding_key, row.immutable_hash) for row in (
            await db.execute(select(DurableFindingModel).where(DurableFindingModel.rule_id == "QF-001"))
        ).scalars())
        assert (await process_qf001_scan(db, scan))[:2] == (5, 0)
        await db.commit()
    second_scan_id = await _qf001_scan(postgres_db, earlier_id, later_id)
    async with postgres_db() as db:
        second_scan = await db.get(AnalysisScanModel, second_scan_id)
        assert (await process_qf001_scan(db, second_scan))[:2] == (5, 0)
        await db.commit()
        rows = list((await db.execute(select(DurableFindingModel).where(
            DurableFindingModel.rule_id == "QF-001"))).scalars())
        assert len(rows) == 5
        assert {row.finding_key: row.immutable_hash for row in rows} == before
        assert not (await db.execute(select(DurableFindingModel).where(
            DurableFindingModel.scan_id == second_scan_id))).scalars().all()


async def test_qf001_transaction_rollback_leaves_no_partial_findings(postgres_db):
    from app.workers.pipeline import process_qf001_scan

    earlier_id, later_id = await _seed_qf001_pair(postgres_db)
    scan_id = await _qf001_scan(postgres_db, earlier_id, later_id)
    async with postgres_db() as db:
        scan = await db.get(AnalysisScanModel, scan_id)
        assert (await process_qf001_scan(db, scan))[:2] == (5, 5)
        await db.rollback()
        assert await db.scalar(select(func.count()).select_from(DurableFindingModel).where(
            DurableFindingModel.scan_id == scan_id)) == 0
        scan = await db.get(AnalysisScanModel, scan_id)
        assert (await process_qf001_scan(db, scan))[:2] == (5, 5)
        await db.commit()


async def test_qf001_incomplete_ingestion_is_rejected_before_finding_writes(postgres_db):
    from app.workers.pipeline import process_qf001_scan

    earlier_id, later_id = await _seed_qf001_pair(postgres_db)
    scan_id = await _qf001_scan(postgres_db, earlier_id, later_id)
    async with postgres_db() as db:
        progress = await db.get(IngestionProgressModel, earlier_id)
        progress.completion_status = "INCOMPLETE"
        await db.commit()
        scan = await db.get(AnalysisScanModel, scan_id)
        with pytest.raises(RuntimeError, match="incomplete or unreconciled"):
            await process_qf001_scan(db, scan)
        await db.rollback()
        assert await db.scalar(select(func.count()).select_from(DurableFindingModel)) == 0


async def test_qf001_observed_records_mode_allows_valid_pairs_from_failed_runs(postgres_db):
    from app.investigations.models import ComparisonEligibilityMode
    from app.workers.pipeline import evaluate_qf001_observations, process_qf001_scan

    earlier_id, later_id = await _seed_qf001_pair(
        postgres_db,
        earlier_run_status="failed",
        earlier_completion="INCOMPLETE",
        earlier_reconciliation="INCOMPLETE",
        later_completion="UNVERIFIED",
        later_reconciliation="UNVERIFIED",
    )
    scan_id = await _qf001_scan(
        postgres_db, earlier_id, later_id,
        eligibility_mode="OBSERVED_RECORDS_ONLY",
        override_reason="Review exact matched historical snapshots only.",
        override_role="manager",
    )
    async with postgres_db() as db:
        read_only_result = await evaluate_qf001_observations(
            db,
            earlier_run_id=earlier_id,
            later_run_id=later_id,
            date_from=date(2026, 8, 26),
            date_to=date(2026, 8, 26),
            eligibility_mode=ComparisonEligibilityMode.OBSERVED_RECORDS_ONLY,
            override_role="manager",
            override_reason="Review exact matched historical snapshots only.",
        )
        assert len(read_only_result.findings) == 5
        assert len(read_only_result.limitations) >= 3
        assert read_only_result.run_statuses[str(earlier_id)] == "failed"
        assert read_only_result.reconciliation_statuses[str(later_id)] == "UNVERIFIED/UNVERIFIED"
        assert await db.scalar(select(func.count()).select_from(DurableFindingModel)) == 0

        scan = await db.get(AnalysisScanModel, scan_id)
        evaluated, inserted, context = await process_qf001_scan(db, scan)
        assert (evaluated, inserted) == (5, 5)
        assert context["eligibility_mode"] == "OBSERVED_RECORDS_ONLY"
        assert context["override_role"] == "manager"
        await db.commit()
        row = await db.scalar(select(DurableFindingModel).where(
            DurableFindingModel.source_session_id == "180660384"))
        assert row.evidence_json["comparison_context"]["reconciliation_limitations"]
        assert row.evidence_json["metadata"]["classification"] == "HISTORICAL_OBSERVATION_ANOMALY"


async def test_qf001_strict_mode_rejects_failed_or_unreconciled_runs(postgres_db):
    from app.workers.pipeline import process_qf001_scan

    earlier_id, later_id = await _seed_qf001_pair(
        postgres_db,
        earlier_run_status="failed",
        earlier_completion="INCOMPLETE",
        earlier_reconciliation="INCOMPLETE",
        later_completion="UNVERIFIED",
        later_reconciliation="UNVERIFIED",
    )
    scan_id = await _qf001_scan(postgres_db, earlier_id, later_id)
    async with postgres_db() as db:
        scan = await db.get(AnalysisScanModel, scan_id)
        with pytest.raises(RuntimeError, match="STRICT_RECONCILED"):
            await process_qf001_scan(db, scan)
        await db.rollback()
        assert await db.scalar(select(func.count()).select_from(DurableFindingModel)) == 0


async def test_observed_records_override_requires_manager_or_admin_and_reason(postgres_db):
    from app.investigations.models import ComparisonEligibilityMode, ScanCreate
    from app.investigations.service import create_scan

    earlier_id, later_id = await _seed_qf001_pair(postgres_db)
    payload = ScanCreate(
        ingestion_run_id=later_id,
        baseline_ingestion_run_id=earlier_id,
        date_from=date(2026, 8, 26), date_to=date(2026, 8, 26),
        requested_by="untrusted", scope="historical_comparison",
        eligibility_mode=ComparisonEligibilityMode.OBSERVED_RECORDS_ONLY,
        eligibility_override_reason="Use matched records for this review.",
    )
    async with postgres_db() as db:
        with pytest.raises(PermissionError):
            await create_scan(db, payload, actor_role="investigator")
        with pytest.raises(ValueError, match="documented reason"):
            await create_scan(db, payload.model_copy(update={"eligibility_override_reason": "too short"}),
                              actor_role="manager")


async def test_qf001_concurrent_scans_deduplicate_atomically(postgres_db):
    from app.workers.pipeline import process_qf001_scan

    earlier_id, later_id = await _seed_qf001_pair(postgres_db)
    scan_ids = [
        await _qf001_scan(postgres_db, earlier_id, later_id),
        await _qf001_scan(postgres_db, earlier_id, later_id),
    ]

    async def execute(scan_id):
        async with postgres_db() as db:
            scan = await db.get(AnalysisScanModel, scan_id)
            result = await process_qf001_scan(db, scan)
            await db.commit()
            return result

    results = await asyncio.gather(*(execute(scan_id) for scan_id in scan_ids))
    assert sorted(inserted for _, inserted, _ in results) == [0, 5]
    async with postgres_db() as db:
        assert await db.scalar(select(func.count()).select_from(DurableFindingModel).where(
            DurableFindingModel.rule_id == "QF-001")) == 5


async def test_qf001_same_identity_with_changed_evidence_raises_conflict(postgres_db):
    from app.investigations.service import ImmutableFindingConflictError, persist_finding

    earlier_id, later_id = await _seed_qf001_pair(postgres_db)
    scan_id = await _qf001_scan(postgres_db, earlier_id, later_id)
    async with postgres_db() as db:
        common = dict(
            scan_id=scan_id, finding_key="QF-001:synthetic-key", rule_id="QF-001",
            severity="medium", confidence=0.65, risk_contribution=15.0,
            reason="review lead", agent_id="synthetic-agent",
            shift_date=date(2026, 8, 26), source_session_id="180660384",
            stable_immutable_hash=True,
        )
        await persist_finding(db, evidence_json={"hash": "original"}, **common)
        await db.commit()
        with pytest.raises(ImmutableFindingConflictError):
            await persist_finding(db, evidence_json={"hash": "changed"}, **common)
        await db.rollback()
        row = await db.scalar(select(DurableFindingModel).where(
            DurableFindingModel.finding_key == "QF-001:synthetic-key"))
        assert row.evidence_json == {"hash": "original"}


async def test_existing_employee_day_finding_persistence_remains_compatible(postgres_db):
    from app.investigations.service import persist_finding

    earlier_id, later_id = await _seed_qf001_pair(postgres_db)
    scan_id = await _qf001_scan(postgres_db, earlier_id, later_id)
    async with postgres_db() as db:
        item = await persist_finding(
            db, scan_id=scan_id, finding_key="agent-1:2026-08-26:SA-R001:s-1:0",
            rule_id="SA-R001", severity="medium", confidence=0.8,
            risk_contribution=10, reason="existing rule", evidence_json={"evidence": []},
        )
        await db.commit()
        assert item is not None
        assert item.rule_id == "SA-R001"


async def test_historical_comparison_scan_api_requires_auth_and_audits_authenticated_actor(
    postgres_db, monkeypatch
):
    from fastapi import Depends, FastAPI
    from httpx import ASGITransport, AsyncClient
    from app.api.v1.routes_investigations import router
    from app.core.auth import Role, require_roles
    from app.core.database import get_db
    from app.core.security import create_access_token

    earlier_id, later_id = await _seed_qf001_pair(postgres_db)
    app = FastAPI()
    app.include_router(
        router,
        prefix="/api/v1",
        dependencies=[Depends(require_roles(Role.INVESTIGATOR, Role.MANAGER, Role.ADMIN))],
    )

    async def override_db():
        async with postgres_db() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(
        "app.api.v1.routes_investigations.celery_app.send_task", lambda *args, **kwargs: None
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        body = {
            "ingestion_run_id": str(later_id),
            "baseline_ingestion_run_id": str(earlier_id),
            "date_from": "2026-08-26",
            "date_to": "2026-08-26",
            "requested_by": "forged-requester",
            "scope": "historical_comparison",
        }
        assert (await client.post("/api/v1/scans", json=body)).status_code == 401
        token = create_access_token("investigator-9", Role.INVESTIGATOR.value)
        response = await client.post(
            "/api/v1/scans", json=body, headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 201
        result = response.json()
        assert result["baseline_ingestion_run_id"] == str(earlier_id)
        scan_id = result["id"]
        observed_body = {
            **body,
            "eligibility_mode": "OBSERVED_RECORDS_ONLY",
            "eligibility_override_reason": "Inspect matched rows in incomplete history.",
        }
        assert (await client.post(
            "/api/v1/scans", json=observed_body,
            headers={"Authorization": f"Bearer {token}"},
        )).status_code == 403
        manager_token = create_access_token("manager-3", Role.MANAGER.value)
        observed_response = await client.post(
            "/api/v1/scans", json=observed_body,
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert observed_response.status_code == 201
        observed_scan_id = observed_response.json()["id"]
    async with postgres_db() as db:
        event = await db.scalar(select(InvestigationAuditEventModel).where(
            InvestigationAuditEventModel.scan_id == scan_id,
            InvestigationAuditEventModel.event_type == "scan_created",
        ))
        assert event.actor == "investigator-9"
        assert event.event_json["baseline_ingestion_run_id"] == str(earlier_id)
        observed_event = await db.scalar(select(InvestigationAuditEventModel).where(
            InvestigationAuditEventModel.scan_id == observed_scan_id,
            InvestigationAuditEventModel.event_type == "scan_created",
        ))
        assert observed_event.actor == "manager-3"
        assert observed_event.event_json["eligibility_mode"] == "OBSERVED_RECORDS_ONLY"
        assert observed_event.event_json["eligibility_override_reason"] == observed_body[
            "eligibility_override_reason"
        ]
