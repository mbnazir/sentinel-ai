from datetime import date, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.weekly.models import PayrollWeek, WeeklyEvidenceQuality, WeeklySession
from app.weekly.activity_comparison import compare_activity_versions
from app.weekly.activity_models import ActivityInterval, ActivityVersion
from datetime import UTC
import app.api.v1.routes_weekly as weekly_routes


def test_weekly_api_requires_auth_and_marks_unreconciled_complete_range_provisional(monkeypatch):
    run_id = uuid4()
    week = PayrollWeek(employee_id="262513", start_date=date(2026, 8, 23), end_date=date(2026, 8, 29),
        ingestion_run_id=run_id, completeness=WeeklyEvidenceQuality.COMPLETE,
        source_count_reconciled=False, provenance={"ingestion_run_status": "completed"})
    session = WeeklySession(source_session_id="180702246", employee_id="262513",
        shift_date=date(2026, 8, 26), start_at=datetime(2026, 8, 26),
        ingestion_run_id=run_id)

    async def fake_load(*args, **kwargs):
        return week, (session,)

    async def fake_db():
        yield object()

    monkeypatch.setattr(weekly_routes, "load_payroll_week", fake_load)
    app.dependency_overrides[get_db] = fake_db
    try:
        with TestClient(app) as client:
            url = f"/api/v1/weekly/262513/2026-08-26?ingestion_run_id={run_id}"
            assert client.get(url).status_code == 401
            token = create_access_token("qa", "viewer")
            response = client.get(url, headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200
            body = response.json()
            assert body["completeness_status"] == "UNVERIFIED"
            assert body["analysis_status"] == "PROVISIONAL"
            assert body["verified_financial_impact_available"] is False
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_activity_change_api_is_authenticated_and_session_scoped(monkeypatch):
    run_id = uuid4()
    start, boundary, end = (datetime(2026, 8, 25, 11, 55, tzinfo=UTC),
                            datetime(2026, 8, 25, 11, 57, 17, tzinfo=UTC),
                            datetime(2026, 8, 25, 12, tzinfo=UTC))

    def activity(activity_id, source, type_id, begin, finish, comment):
        return ActivityInterval(activity_id=activity_id, data_source_id=source,
            activity_type_id=type_id, start_at=begin, end_at=finish,
            duration_seconds=None, comment=comment, source_system="quartz",
            source_session_id="180596739", ingestion_run_id=run_id)

    old = ActivityVersion(ingestion_run_id=run_id, source_system="quartz",
        source_session_id="180596739", data_source_id=2, version_id="source-2",
        activities=(activity("a", 2, 2, start, end, "bio"),))
    new = ActivityVersion(ingestion_run_id=run_id, source_system="quartz",
        source_session_id="180596739", data_source_id=3, version_id="source-3",
        activities=(activity("b", 3, 2, start, boundary, "edited"),
                    activity("c", 3, 7, boundary, end, "OT Break")))
    comparison = compare_activity_versions(old, new, ingestion_run_id=run_id,
        source_system="quartz", source_session_id="180596739", original_source_id=2,
        revised_source_id=3)

    async def fake_load(*args, **kwargs):
        if kwargs["employee_id"] != "agent-1" or kwargs["source_session_id"] != "180596739":
            return None
        return comparison

    async def fake_db():
        yield object()

    monkeypatch.setattr(weekly_routes, "load_activity_comparison", fake_load)
    app.dependency_overrides[get_db] = fake_db
    try:
        with TestClient(app) as client:
            url = f"/api/v1/weekly/agent-1/2026-08-26/activity-changes?ingestion_run_id={run_id}&source_session_id=180596739"
            assert client.get(url).status_code == 401
            token = create_access_token("qa", "investigator")
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get(url, headers=headers)
            assert response.status_code == 200
            payload = response.json()
            assert payload["finding"]["code"] == "WF-005"
            assert payload["finding"]["editor_identity"] == "UNVERIFIED"
            assert payload["finding"]["financial_impact"] == "UNVERIFIED"
            assert payload["change_summary"]["net_covered_seconds"] == "0"
            assert any(change["change_type"] == "RECLASSIFIED"
                       and change["affected_seconds"] == "163"
                       for change in payload["interval_changes"])
            denied = client.get(url.replace("agent-1", "agent-2"), headers=headers)
            assert denied.status_code == 404
    finally:
        app.dependency_overrides.pop(get_db, None)
