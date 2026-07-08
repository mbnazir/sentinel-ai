from datetime import datetime
from app.timeline.domain.activity_snapshot import ActivitySnapshot
from app.timeline.domain.timeline import Timeline
from app.timeline.domain.timeline_segment import TimelineSegment

class TimelineBuilder:
    """Build a normalized atomic timeline from all activity source versions."""

    def build(self, login_session_external_id: str, activities: list[ActivitySnapshot]) -> Timeline:
        closed = [activity for activity in activities if activity.end_time is not None]
        boundaries = self._collect_boundaries(closed)
        if len(boundaries) < 2:
            return Timeline(login_session_external_id=login_session_external_id, segments=[])

        segments = []
        for index in range(len(boundaries) - 1):
            start = boundaries[index]
            end = boundaries[index + 1]
            if start >= end:
                continue

            by_source = {}
            for activity in closed:
                if activity.overlaps(start, end):
                    by_source.setdefault(activity.data_source, []).append(activity)

            if by_source:
                segments.append(TimelineSegment(start, end, by_source))

        return Timeline(login_session_external_id=login_session_external_id, segments=segments)

    def _collect_boundaries(self, activities: list[ActivitySnapshot]) -> list[datetime]:
        boundaries = set()
        for activity in activities:
            boundaries.add(activity.start_time)
            if activity.end_time:
                boundaries.add(activity.end_time)
        return sorted(boundaries)
