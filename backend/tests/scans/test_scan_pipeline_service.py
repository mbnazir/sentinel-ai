from datetime import date, datetime, timezone

from app.scans.domain.scan_models import ScanRequest
from app.scans.services.scan_pipeline_service import ScanPipelineService


class FakeSession:
    external_id = "LS1"


class FakeActivity:
    def __init__(self, external_id, source, start, end, duration):
        self.external_id = external_id
        self.login_session_external_id = "LS1"
        self.source = source
        self.activity_type = "1"
        self.start_time = start
        self.end_time = end
        self.duration_seconds = duration
        self.agent_external_id = "AG1"
        self.comment = None


class FakeRepository:
    def list_sessions_for_shift_range(self, organization_id, shift_date_from, shift_date_to):
        return [FakeSession()]

    def list_activities_for_session(self, organization_id, login_session_external_id):
        return [
            FakeActivity("SYS1", "System", datetime(2026, 7, 1, 8, tzinfo=timezone.utc), datetime(2026, 7, 1, 9, tzinfo=timezone.utc), 3600),
            FakeActivity("AG1", "Agent", datetime(2026, 7, 1, 8, tzinfo=timezone.utc), datetime(2026, 7, 1, 10, tzinfo=timezone.utc), 7200),
        ]


def test_scan_pipeline_scores_session() -> None:
    summary = ScanPipelineService(FakeRepository()).run(
        ScanRequest(
            organization_id="ORG1",
            shift_date_from=date(2026, 7, 1),
            shift_date_to=date(2026, 7, 1),
        )
    )

    assert summary.sessions_scanned == 1
    assert summary.results[0].login_session_external_id == "LS1"
    assert summary.results[0].risk_score > 0
    assert summary.results[0].rule_count > 0
