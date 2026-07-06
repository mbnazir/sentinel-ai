from app.matcher.domain.match_result import ActivityMatch
from app.matcher.services.activity_matcher import ActivityMatcher
from app.timeline.domain.source import DataSource
from app.timeline.domain.timeline import Timeline


class SourceMatchService:
    """Matches activities between a baseline source and a comparison source."""

    def __init__(self, matcher: ActivityMatcher | None = None) -> None:
        self.matcher = matcher or ActivityMatcher()

    def match_timeline_sources(
        self,
        timeline: Timeline,
        baseline_source: DataSource,
        comparison_source: DataSource,
    ) -> list[ActivityMatch]:
        baseline = timeline.get_source_activities(baseline_source)
        comparison = timeline.get_source_activities(comparison_source)
        return self.matcher.match_sources(
            baseline_activities=baseline,
            comparison_activities=comparison,
            baseline_source=baseline_source,
            comparison_source=comparison_source,
        )
