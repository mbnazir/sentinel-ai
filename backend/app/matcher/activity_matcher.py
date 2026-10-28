from datetime import datetime

from app.domain.data_sources import ActivityDataSource
from app.matcher.models import ActivityChangeType, ActivityMatch, SourceComparison
from app.timeline.models import TimelineActivity

MATCH_THRESHOLD = 0.35
BOUNDARY_WINDOW_SECONDS = 300


def compare_activity_versions(
    *,
    source_session_id: str,
    baseline_source: ActivityDataSource,
    comparison_source: ActivityDataSource,
    baseline: list[TimelineActivity],
    comparison: list[TimelineActivity],
) -> SourceComparison:
    """Greedily match activities using temporal overlap, type agreement and boundary proximity."""
    candidates: list[tuple[float, int, int]] = []
    for baseline_index, left in enumerate(baseline):
        for comparison_index, right in enumerate(comparison):
            score = _match_score(left, right)
            if score >= MATCH_THRESHOLD:
                candidates.append((score, baseline_index, comparison_index))

    used_baseline: set[int] = set()
    used_comparison: set[int] = set()
    matches: list[ActivityMatch] = []
    for score, baseline_index, comparison_index in sorted(candidates, reverse=True):
        if baseline_index in used_baseline or comparison_index in used_comparison:
            continue
        used_baseline.add(baseline_index)
        used_comparison.add(comparison_index)
        matches.append(
            _matched_result(
                baseline_source,
                comparison_source,
                baseline[baseline_index],
                comparison[comparison_index],
                score,
            )
        )

    for index, activity in enumerate(baseline):
        if index not in used_baseline:
            matches.append(_removed_result(baseline_source, comparison_source, activity))
    for index, activity in enumerate(comparison):
        if index not in used_comparison:
            matches.append(_inserted_result(baseline_source, comparison_source, activity))

    matches.sort(key=_sort_key)
    return SourceComparison(
        source_session_id=source_session_id,
        baseline_source=baseline_source,
        comparison_source=comparison_source,
        matches=tuple(matches),
    )


def _match_score(left: TimelineActivity, right: TimelineActivity) -> float:
    overlap = _overlap_seconds(left.start_at, left.end_at, right.start_at, right.end_at)
    left_duration = max(left.duration_seconds, 1)
    right_duration = max(right.duration_seconds, 1)
    overlap_ratio = overlap / max(left_duration, right_duration)
    type_score = 1.0 if left.activity_type_id == right.activity_type_id else 0.0
    boundary_score = _boundary_score(left, right)
    return round((0.60 * overlap_ratio) + (0.25 * type_score) + (0.15 * boundary_score), 6)


def _boundary_score(left: TimelineActivity, right: TimelineActivity) -> float:
    start_delta = abs((right.start_at - left.start_at).total_seconds())
    end_delta = _end_delta(left.end_at, right.end_at)
    start_score = max(0.0, 1.0 - (start_delta / BOUNDARY_WINDOW_SECONDS))
    end_score = 0.0 if end_delta is None else max(0.0, 1.0 - (abs(end_delta) / BOUNDARY_WINDOW_SECONDS))
    return (start_score + end_score) / 2


def _matched_result(
    baseline_source: ActivityDataSource,
    comparison_source: ActivityDataSource,
    left: TimelineActivity,
    right: TimelineActivity,
    confidence: float,
) -> ActivityMatch:
    overlap = _overlap_seconds(left.start_at, left.end_at, right.start_at, right.end_at)
    duration_delta = right.duration_seconds - left.duration_seconds
    start_delta = int((right.start_at - left.start_at).total_seconds())
    end_delta = _end_delta(left.end_at, right.end_at)
    type_changed = left.activity_type_id != right.activity_type_id
    return ActivityMatch(
        baseline_source=baseline_source,
        comparison_source=comparison_source,
        baseline_activity=left,
        comparison_activity=right,
        confidence=confidence,
        overlap_seconds=overlap,
        overlap_ratio=round(overlap / max(left.duration_seconds, right.duration_seconds, 1), 6),
        start_delta_seconds=start_delta,
        end_delta_seconds=end_delta,
        duration_delta_seconds=duration_delta,
        activity_type_changed=type_changed,
        change_type=_classify_change(start_delta, end_delta, duration_delta, type_changed),
    )


def _removed_result(
    baseline_source: ActivityDataSource,
    comparison_source: ActivityDataSource,
    activity: TimelineActivity,
) -> ActivityMatch:
    return ActivityMatch(
        baseline_source=baseline_source,
        comparison_source=comparison_source,
        baseline_activity=activity,
        comparison_activity=None,
        confidence=1.0,
        overlap_seconds=0,
        overlap_ratio=0.0,
        start_delta_seconds=None,
        end_delta_seconds=None,
        duration_delta_seconds=-activity.duration_seconds,
        activity_type_changed=False,
        change_type=ActivityChangeType.REMOVED,
    )


def _inserted_result(
    baseline_source: ActivityDataSource,
    comparison_source: ActivityDataSource,
    activity: TimelineActivity,
) -> ActivityMatch:
    return ActivityMatch(
        baseline_source=baseline_source,
        comparison_source=comparison_source,
        baseline_activity=None,
        comparison_activity=activity,
        confidence=1.0,
        overlap_seconds=0,
        overlap_ratio=0.0,
        start_delta_seconds=None,
        end_delta_seconds=None,
        duration_delta_seconds=activity.duration_seconds,
        activity_type_changed=False,
        change_type=ActivityChangeType.INSERTED,
    )


def _classify_change(
    start_delta: int, end_delta: int | None, duration_delta: int, type_changed: bool
) -> ActivityChangeType:
    boundary_changed = start_delta != 0 or (end_delta is not None and end_delta != 0)
    if type_changed and boundary_changed:
        return ActivityChangeType.COMPOUND
    if type_changed:
        return ActivityChangeType.TYPE_CHANGED
    if start_delta == 0 and (end_delta in (None, 0)) and duration_delta == 0:
        return ActivityChangeType.UNCHANGED
    if duration_delta > 0 and start_delta <= 0 and (end_delta is None or end_delta >= 0):
        return ActivityChangeType.EXTENDED
    if duration_delta < 0 and start_delta >= 0 and (end_delta is None or end_delta <= 0):
        return ActivityChangeType.SHORTENED
    if duration_delta == 0 and boundary_changed:
        return ActivityChangeType.SHIFTED
    return ActivityChangeType.COMPOUND


def _overlap_seconds(
    left_start: datetime,
    left_end: datetime | None,
    right_start: datetime,
    right_end: datetime | None,
) -> int:
    if left_end is None or right_end is None:
        return 0
    start = max(left_start, right_start)
    end = min(left_end, right_end)
    return max(0, int((end - start).total_seconds()))


def _end_delta(left_end: datetime | None, right_end: datetime | None) -> int | None:
    if left_end is None or right_end is None:
        return None
    return int((right_end - left_end).total_seconds())


def _sort_key(item: ActivityMatch) -> tuple[datetime, str]:
    activity = item.comparison_activity or item.baseline_activity
    assert activity is not None
    return activity.start_at, item.change_type.value
