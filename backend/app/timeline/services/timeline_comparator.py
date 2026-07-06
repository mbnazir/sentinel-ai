from app.timeline.domain.source import DataSource
from app.timeline.domain.timeline import Timeline
from app.timeline.domain.timeline_comparison import SourceDurationComparison, TimelineComparison

class TimelineComparator:
    def compare_against_baseline(self, timeline: Timeline, baseline_source: DataSource) -> TimelineComparison:
        totals = timeline.total_seconds_by_source()
        baseline_seconds = totals[baseline_source]
        comparisons = [
            SourceDurationComparison(source, seconds, baseline_seconds)
            for source, seconds in totals.items()
            if source != baseline_source and seconds > 0
        ]
        return TimelineComparison(timeline.login_session_external_id, baseline_source, comparisons)
