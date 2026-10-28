from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import IngestionRunModel, SessionSnapshotModel
from app.weekly.models import PayrollWeek, WeeklyEvidenceQuality, WeeklySession
from app.weekly.payable import resolve_session_payable


def week_bounds(day: date) -> tuple[date, date]:
    start = day - timedelta(days=(day.weekday() + 1) % 7)
    return start, start + timedelta(days=6)


async def load_payroll_week(db: AsyncSession, *, ingestion_run_id: UUID,
                            employee_id: str, day: date) -> tuple[PayrollWeek, tuple[WeeklySession, ...]]:
    start, end = week_bounds(day)
    run = await db.get(IngestionRunModel, ingestion_run_id)
    rows = list((await db.execute(select(SessionSnapshotModel).where(
        SessionSnapshotModel.ingestion_run_id == ingestion_run_id,
        SessionSnapshotModel.agent_id == employee_id,
        SessionSnapshotModel.shift_date >= start,
        SessionSnapshotModel.shift_date <= end,
    ).order_by(SessionSnapshotModel.shift_date, SessionSnapshotModel.start_at))).scalars())
    # A completed date-range pull is not source reconciliation. It cannot be called complete
    # until Quartz provides comparable expected record counts for the full range.
    range_covered = bool(run and run.shift_date_from <= start and run.shift_date_to >= end)
    failed = not run or run.status in {"failed", "cancelled", "queued", "running"} or not range_covered
    quality = (WeeklyEvidenceQuality.INCOMPLETE if failed else
               WeeklyEvidenceQuality.UNVERIFIED)
    observed_dates = {r.shift_date for r in rows}
    missing_dates = tuple(d for d in (start + timedelta(days=i) for i in range(7))
                          if d not in observed_dates)
    week = PayrollWeek(employee_id=employee_id, start_date=start, end_date=end,
                       ingestion_run_id=ingestion_run_id,
                       completeness=quality, missing_dates=missing_dates,
                       received_record_count=(run.session_count if run else None),
                       source_record_count=None, source_count_reconciled=False,
                       provenance={"ingestion_run_status": run.status if run else "missing",
                                   "run_range_covers_week": range_covered,
                                   "employee_dates_without_sessions": [d.isoformat() for d in missing_dates],
                                   "source_count_reconciled": False,
                                   "note": "No Quartz expected record count contract is available"})
    sessions = tuple(WeeklySession(source_session_id=r.source_session_id, employee_id=r.agent_id,
                    shift_date=r.shift_date, start_at=r.start_at, end_at=r.end_at,
                    ingestion_run_id=r.ingestion_run_id, supervisor_id=r.supervisor_id,
                    manager_id=r.manager_id, metadata=r.metadata_json,
                    payable=resolve_session_payable(r.metadata_json)) for r in rows)
    overlaps = []
    ordered = sorted((s for s in sessions if s.end_at is not None), key=lambda s: s.start_at)
    for index, left in enumerate(ordered):
        for right in ordered[index + 1:]:
            if right.start_at >= left.end_at:
                break
            if left.source_session_id != right.source_session_id:
                overlaps.append({"session_a": left.source_session_id,
                                 "session_b": right.source_session_id,
                                 "start_at": right.start_at.isoformat(),
                                 "end_at": min(left.end_at, right.end_at).isoformat()})
    week = week.model_copy(update={"provenance": {**week.provenance,
                                                   "overlapping_session_pairs": overlaps}})
    return week, sessions
