from datetime import date, datetime, timezone

from app.application.normalized import NormalizedLoginSession
from app.application.snapshot_hash import canonical_hash


def test_snapshot_hash_is_deterministic_and_changes_with_evidence() -> None:
    base = NormalizedLoginSession(
        source_system="quartz",
        source_session_id="100",
        agent_id="42",
        shift_date=date(2026, 8, 26),
        start_at=datetime(2026, 8, 26, 8, tzinfo=timezone.utc),
        ready_for_payroll=True,
    )
    changed = base.model_copy(update={"ready_for_payroll": False})
    assert canonical_hash(base) == canonical_hash(base)
    assert canonical_hash(base) != canonical_hash(changed)
