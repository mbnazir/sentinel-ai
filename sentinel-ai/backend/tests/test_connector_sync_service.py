from datetime import date, datetime, timezone

import pytest

from app.application.interfaces.connector import Connector
from app.application.services.connector_sync_service import ConnectorSyncService
from app.domain.entities.activity import Activity
from app.domain.entities.login_session import LoginSession


class FakeRepository:
    def __init__(self, db: object) -> None:
        self.sessions = []
        self.activities = []

    def upsert_session(self, organization_id, connector_id, connector_run_id, session):
        self.sessions.append(session)
        return type("Persisted", (), {"id": len(self.sessions)})()

    def upsert_activity(self, organization_id, connector_id, connector_run_id, normalized_session_id, activity):
        self.activities.append(activity)
        return type("Persisted", (), {"id": len(self.activities)})()


class FakeDb:
    def commit(self) -> None:
        pass


class FakeConnector(Connector):
    async def test_connection(self) -> bool:
        return True

    async def get_sessions(self, shift_date_from: date, shift_date_to: date):
        return [
            LoginSession(
                external_id="LS1",
                agent_external_id="A1",
                supervisor_external_id="S1",
                shift_date=shift_date_from,
                start_time=datetime(2026, 7, 1, 8, tzinfo=timezone.utc),
                end_time=None,
            )
        ]

    async def get_activities(self, login_session_external_ids: list[str]):
        return [
            Activity(
                external_id="ACT1",
                login_session_external_id="LS1",
                agent_external_id="A1",
                source="system",
                activity_type="work",
                start_time=datetime(2026, 7, 1, 8, tzinfo=timezone.utc),
                end_time=datetime(2026, 7, 1, 9, tzinfo=timezone.utc),
                duration_seconds=3600,
            )
        ]


@pytest.mark.asyncio
async def test_connector_sync_summary(monkeypatch) -> None:
    import app.application.services.connector_sync_service as module

    monkeypatch.setattr(module, "NormalizedWorkforceRepository", FakeRepository)
    service = ConnectorSyncService(
        db=FakeDb(),
        connector=FakeConnector(),
        organization_id=1,
        connector_id=2,
    )

    summary = await service.synchronize_shift_dates(date(2026, 7, 1), date(2026, 7, 5))

    assert summary.sessions_imported == 1
    assert summary.activities_imported == 1
    assert summary.activities_skipped == 0
