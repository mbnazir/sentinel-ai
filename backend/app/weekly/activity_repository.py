from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import ActivitySnapshotModel, SessionSnapshotModel
from app.weekly.activity_comparison import compare_activity_versions
from app.weekly.activity_models import ActivityInterval, ActivityVersion, VersionComparison
from app.weekly.builder import week_bounds


async def load_activity_comparison(
    db: AsyncSession,
    *,
    ingestion_run_id: UUID,
    employee_id: str,
    day: date,
    source_session_id: str,
    original_source_id: int = 2,
    revised_source_id: int = 3,
) -> VersionComparison | None:
    start, end = week_bounds(day)
    session_result = await db.execute(select(SessionSnapshotModel).where(
        SessionSnapshotModel.ingestion_run_id == ingestion_run_id,
        SessionSnapshotModel.source_system == "quartz",
        SessionSnapshotModel.source_session_id == source_session_id,
        SessionSnapshotModel.agent_id == employee_id,
        SessionSnapshotModel.shift_date >= start,
        SessionSnapshotModel.shift_date <= end,
    ))
    session = session_result.scalar_one_or_none()
    if session is None:
        return None

    activity_result = await db.execute(select(ActivitySnapshotModel).where(
        ActivitySnapshotModel.ingestion_run_id == ingestion_run_id,
        ActivitySnapshotModel.source_system == session.source_system,
        ActivitySnapshotModel.source_session_id == session.source_session_id,
    ).order_by(ActivitySnapshotModel.data_source_id, ActivitySnapshotModel.start_at,
               ActivitySnapshotModel.source_activity_id))
    rows = list(activity_result.scalars())
    grouped: dict[int, list[ActivityInterval]] = {}
    for row in rows:
        grouped.setdefault(row.data_source_id, []).append(ActivityInterval(
            activity_id=row.source_activity_id,
            data_source_id=row.data_source_id,
            activity_type_id=row.activity_type_id,
            start_at=row.start_at,
            end_at=row.end_at,
            duration_seconds=row.duration_seconds,
            comment=row.comment,
            source_created_at=row.source_created_at,
            source_updated_at=row.source_updated_at,
            source_system=row.source_system,
            source_session_id=row.source_session_id,
            ingestion_run_id=row.ingestion_run_id,
        ))

    def make_version(source_id: int) -> ActivityVersion | None:
        if source_id not in grouped:
            return None
        return ActivityVersion(ingestion_run_id=ingestion_run_id, source_system=session.source_system,
            source_session_id=session.source_session_id, data_source_id=source_id,
            version_id=f"quartz-source-{source_id}", activities=tuple(grouped[source_id]))

    return compare_activity_versions(make_version(original_source_id), make_version(revised_source_id),
        ingestion_run_id=ingestion_run_id, source_system=session.source_system,
        source_session_id=session.source_session_id, original_source_id=original_source_id,
        revised_source_id=revised_source_id)
