from datetime import date, datetime, timezone

from app.connectors.quartz.services.quartz_ingestion_service import QuartzIngestionResult
from app.connectors.quartz.services.quartz_persisted_ingestion_service import QuartzPersistedIngestionService
from app.domain.entities.activity import Activity
from app.domain.entities.login_session import LoginSession


class FakeIngestionService:
    async def ingest_shift_date_range(self, shift_date_from, shift_date_to):
        return QuartzIngestionResult(
            sessions=[
                LoginSession(
                    external_id="LS-1",
                    agent_external_id="A1",
                    supervisor_external_id="S1",
                    shift_date=date(2026, 7, 1),
                    start_time=datetime(2026, 7, 1, 8, tzinfo=timezone.utc),
                    end_time=datetime(2026, 7, 1, 17, tzinfo=timezone.utc),
                    status="1",
                )
            ],
            activities=[
                Activity(
                    external_id="ACT-1",
                    login_session_external_id="LS-1",
                    agent_external_id="A1",
                    source="System",
                    activity_type="1",
                    start_time=datetime(2026, 7, 1, 8, tzinfo=timezone.utc),
                    end_time=datetime(2026, 7, 1, 9, tzinfo=timezone.utc),
                    duration_seconds=3600,
                )
            ],
            session_count=1,
            activity_count=1,
        )


class FakeRepository:
    def upsert_sessions(self, organization_id, connector_type, sessions):
        assert organization_id == "ORG1"
        assert connector_type == "quartz"
        return len(sessions)

    def upsert_activities(self, organization_id, connector_type, activities):
        assert organization_id == "ORG1"
        assert connector_type == "quartz"
        return len(activities)


async def test_persisted_ingestion_service_persists_result() -> None:
    service = QuartzPersistedIngestionService(FakeIngestionService(), FakeRepository())

    result = await service.ingest_and_persist("ORG1", date(2026, 7, 1), date(2026, 7, 1))

    assert result.fetched_sessions == 1
    assert result.fetched_activities == 1
    assert result.persisted_sessions == 1
    assert result.persisted_activities == 1
