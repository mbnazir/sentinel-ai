from dataclasses import dataclass, field

from app.matcher.domain.match_result import ActivityMatch
from app.timeline.domain.source import DataSource
from app.timeline.domain.timeline import Timeline


@dataclass(frozen=True)
class RuleContext:
    login_session_external_id: str
    timeline: Timeline
    matches_by_source_pair: dict[tuple[DataSource, DataSource], list[ActivityMatch]] = field(default_factory=dict)

    def matches(self, baseline: DataSource, comparison: DataSource) -> list[ActivityMatch]:
        return self.matches_by_source_pair.get((baseline, comparison), [])
