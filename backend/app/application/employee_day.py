from collections import defaultdict
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.data_sources import ActivityDataSource
from app.infrastructure.models import ActivitySnapshotModel, SessionSnapshotModel


class ActivitySummary(BaseModel):
    data_source_id: int
    data_source: str
    activity_count: int
    duration_seconds: int


class EmployeeDaySession(BaseModel):
    source_session_id: str
    start_at: datetime
    end_at: datetime | None
    ready_for_payroll: bool
    payroll_adjusted: bool
    session_added_by: str | None
    multiple_logins: int


class EmployeeDaySnapshot(BaseModel):
    ingestion_run_id: UUID
    agent_id: str
    shift_date: date
    session_count: int
    sessions: list[EmployeeDaySession]
    activity_summary: list[ActivitySummary]


async def load_employee_day(
    db: AsyncSession, *, ingestion_run_id: UUID, agent_id: str, shift_date: date
) -> EmployeeDaySnapshot | None:
    session_result = await db.execute(
        select(SessionSnapshotModel)
        .where(
            SessionSnapshotModel.ingestion_run_id == ingestion_run_id,
            SessionSnapshotModel.agent_id == agent_id,
            SessionSnapshotModel.shift_date == shift_date,
        )
        .order_by(SessionSnapshotModel.start_at)
    )
    session_rows = list(session_result.scalars())
    if not session_rows:
        return None

    session_ids = [row.source_session_id for row in session_rows]
    activity_result = await db.execute(
        select(ActivitySnapshotModel).where(
            ActivitySnapshotModel.ingestion_run_id == ingestion_run_id,
            ActivitySnapshotModel.source_session_id.in_(session_ids),
        )
    )
    totals: dict[int, list[int]] = defaultdict(lambda: [0, 0])
    for row in activity_result.scalars():
        totals[row.data_source_id][0] += 1
        totals[row.data_source_id][1] += row.duration_seconds or 0

    return EmployeeDaySnapshot(
        ingestion_run_id=ingestion_run_id,
        agent_id=agent_id,
        shift_date=shift_date,
        session_count=len(session_rows),
        sessions=[
            EmployeeDaySession(
                source_session_id=row.source_session_id,
                start_at=row.start_at,
                end_at=row.end_at,
                ready_for_payroll=row.ready_for_payroll,
                payroll_adjusted=row.payroll_adjusted,
                session_added_by=row.session_added_by,
                multiple_logins=row.multiple_logins,
            )
            for row in session_rows
        ],
        activity_summary=[
            ActivitySummary(
                data_source_id=source_id,
                data_source=_source_label(source_id),
                activity_count=values[0],
                duration_seconds=values[1],
            )
            for source_id, values in sorted(totals.items())
        ],
    )


def _source_label(value: int) -> str:
    try:
        return ActivityDataSource(value).label
    except ValueError:
        return f"Unknown({value})"
