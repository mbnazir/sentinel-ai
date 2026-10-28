from decimal import Decimal

from app.weekly.models import ActorStatus, WeeklyAdjustment


def attribute_adjustments(*, employee_id: str, sessions, activities) -> tuple[WeeklyAdjustment, ...]:
    """Return supported positive manual activity revisions; activity source alone isn't actor proof."""
    by_session = {s.source_session_id: s for s in sessions}
    seen: set[str] = set()
    out = []
    for a in activities:
        session = by_session.get(a.source_session_id)
        if session is None or a.source_activity_id in seen or a.data_source_id < 3:
            continue
        raw_before = a.metadata.get("before_seconds")
        raw_after = a.metadata.get("after_seconds")
        try:
            before, after = Decimal(str(raw_before)), Decimal(str(raw_after))
        except Exception:
            continue
        if not before.is_finite() or not after.is_finite() or after <= before:
            continue
        seen.add(a.source_activity_id)
        editor = a.metadata.get("editor_id")
        actor_field = a.metadata.get("actor_id")
        if editor and actor_field and str(editor) != str(actor_field):
            actor = None
            actor_status = ActorStatus.CONFLICTING
        else:
            actor = editor or actor_field
            # Identity is not verified just because a source record names it. Verification
            # requires an explicit, trusted source assertion.
            actor_status = (ActorStatus.VERIFIED if actor and a.metadata.get("actor_verified") is True
                            else ActorStatus.ACTOR_UNVERIFIED)
        out.append(WeeklyAdjustment(adjustment_id=a.source_activity_id, employee_id=employee_id,
            source_session_id=a.source_session_id, source_activity_id=a.source_activity_id,
            shift_date=session.shift_date, delta_seconds=after-before,
            actor_id=str(actor) if actor else "ACTOR_UNVERIFIED",
            actor_status=actor_status,
            before_seconds=before, after_seconds=after, action_at=a.updated_at or a.created_at,
            data_source_id=int(a.data_source_id), provenance=("Activity explicit before/after metadata",)))
    return tuple(out)
