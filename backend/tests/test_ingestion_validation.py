from datetime import date, datetime, timezone

import pytest

from app.application.ingestion import IngestionRangeError, SnapshotIngestionService
from app.application.normalized import NormalizedActivity, NormalizedLoginSession
from app.domain.data_sources import ActivityDataSource


def session(session_id: str, shift_date: date) -> NormalizedLoginSession:
    return NormalizedLoginSession(
        source_system="quartz",
        source_session_id=session_id,
        agent_id="42",
        shift_date=shift_date,
        start_at=datetime(2026, 8, 26, 8, tzinfo=timezone.utc),
    )


def test_session_validation_preserves_multiple_sessions_for_same_employee_day() -> None:
    items = [session("100", date(2026, 8, 26)), session("101", date(2026, 8, 26))]
    SnapshotIngestionService._validate_session_batch(items, date(2026, 8, 26), date(2026, 8, 26))


def test_session_validation_rejects_duplicate_source_session_id() -> None:
    items = [session("100", date(2026, 8, 26)), session("100", date(2026, 8, 26))]
    with pytest.raises(ValueError, match="duplicate source session id"):
        SnapshotIngestionService._validate_session_batch(items, date(2026, 8, 26), date(2026, 8, 26))


def test_activity_validation_rejects_activity_outside_imported_sessions() -> None:
    item = NormalizedActivity(
        source_system="quartz",
        source_activity_id="500",
        source_session_id="999",
        data_source_id=ActivityDataSource.AGENT,
        activity_type_id=1,
        start_at=datetime(2026, 8, 26, 8, tzinfo=timezone.utc),
        end_at=None,
        duration_seconds=60,
    )
    with pytest.raises(ValueError, match="unexpected login session"):
        SnapshotIngestionService._validate_activity_batch([item], {"100"})


def test_ingestion_range_error_type() -> None:
    assert issubclass(IngestionRangeError, ValueError)
