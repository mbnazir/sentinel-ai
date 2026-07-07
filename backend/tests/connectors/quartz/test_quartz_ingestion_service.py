from datetime import date

from app.connectors.quartz.client.quartz_api_models import QuartzPage
from app.connectors.quartz.services.quartz_ingestion_service import QuartzIngestionService


class FakeQuartzClient:
    async def fetch_sessions_page(self, shift_date_from, shift_date_to, cursor=None):
        return QuartzPage(
            items=[
                {
                    "id": 100,
                    "agent_id": 10,
                    "supervisor_id": 20,
                    "manager_id": None,
                    "shift_date": "2026-07-01",
                    "start_date": "2026-07-01T08:00:00+00:00",
                    "end_date": "2026-07-01T17:00:00+00:00",
                    "status_id": 1,
                }
            ],
            next_cursor=None,
        )

    async def fetch_activities_batch(self, login_session_ids):
        return [
            {
                "id": 1,
                "login_session_id": 100,
                "agent_id": 10,
                "data_source_id": 1,
                "activity_type_id": 1,
                "source_id": 5,
                "start_time": "2026-07-01T08:00:00+00:00",
                "end_time": "2026-07-01T09:00:00+00:00",
                "duration": 3600,
                "comment": None,
            }
        ]


async def test_ingestion_service_loads_sessions_and_activities() -> None:
    result = await QuartzIngestionService(FakeQuartzClient()).ingest_shift_date_range(
        date(2026, 7, 1),
        date(2026, 7, 1),
    )

    assert result.session_count == 1
    assert result.activity_count == 1
    assert result.sessions[0].external_id == "100"
    assert result.activities[0].source == "System"
