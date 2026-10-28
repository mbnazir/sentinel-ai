from collections import defaultdict
from dataclasses import dataclass

from app.domain.data_sources import ActivityDataSource
from app.timeline.analysis import EmployeeDayAnalysis
from app.timeline.models import TimelineActivity, TimelineSession


@dataclass(frozen=True, slots=True)
class IntegrityPolicy:
    large_addition_seconds: int = 3600
    captured_evidence_low_seconds: int = 3 * 3600
    final_vs_capture_tolerance_seconds: int = 30 * 60
    phone_system_mismatch_seconds: int = 60 * 60
    rounded_increment_seconds: int = 30 * 60
    minimum_rounded_addition_seconds: int = 30 * 60
    excessive_day_seconds: int = 12 * 3600
    repeated_modified_sessions_threshold: int = 2


@dataclass(frozen=True, slots=True)
class RuleContext:
    analysis: EmployeeDayAnalysis
    policy: IntegrityPolicy

    def session(self, source_session_id: str) -> TimelineSession:
        return next(
            session
            for session in self.analysis.timeline.sessions
            if session.source_session_id == source_session_id
        )

    def source_activities(
        self,
        session: TimelineSession,
        source: ActivityDataSource,
    ) -> list[TimelineActivity]:
        return [activity for activity in session.activities if activity.data_source_id == source]

    def source_seconds(self, session: TimelineSession, source: ActivityDataSource) -> int:
        return sum(activity.duration_seconds for activity in self.source_activities(session, source))

    def session_source_totals(self, session: TimelineSession) -> dict[ActivityDataSource, int]:
        totals: dict[ActivityDataSource, int] = defaultdict(int)
        for activity in session.activities:
            totals[activity.data_source_id] += activity.duration_seconds
        return dict(totals)

    def captured_seconds(self, session: TimelineSession) -> int:
        return max(
            self.source_seconds(session, ActivityDataSource.PHONE),
            self.source_seconds(session, ActivityDataSource.SYSTEM),
        )

    def latest_manual_seconds(self, session: TimelineSession) -> tuple[ActivityDataSource | None, int]:
        for source in (
            ActivityDataSource.PAYROLL,
            ActivityDataSource.MANAGER,
            ActivityDataSource.SUPERVISOR,
            ActivityDataSource.AGENT,
        ):
            seconds = self.source_seconds(session, source)
            if seconds > 0:
                return source, seconds
        return None, 0
