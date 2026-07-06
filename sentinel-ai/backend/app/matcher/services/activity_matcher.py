from app.matcher.domain.match_result import (
    ActivityMatch,
    ActivityMatchScore,
    MatchClassification,
)
from app.timeline.domain.activity_snapshot import ActivitySnapshot
from app.timeline.domain.source import DataSource


class ActivityMatcher:
    """Confidence-based matcher for comparing activity versions.

    Matching never uses activity IDs because source versions can create different IDs.
    It uses time overlap, start/end proximity, duration similarity, and activity-type similarity.
    """

    def __init__(self, minimum_match_confidence: float = 0.55) -> None:
        self.minimum_match_confidence = minimum_match_confidence

    def match_sources(
        self,
        baseline_activities: list[ActivitySnapshot],
        comparison_activities: list[ActivitySnapshot],
        baseline_source: DataSource,
        comparison_source: DataSource,
    ) -> list[ActivityMatch]:
        unmatched_baseline = list(baseline_activities)
        unmatched_comparison = list(comparison_activities)
        matches: list[ActivityMatch] = []

        candidate_pairs = []
        for baseline in unmatched_baseline:
            for comparison in unmatched_comparison:
                score = self.score_pair(baseline, comparison)
                candidate_pairs.append((score.total, baseline, comparison, score))

        candidate_pairs.sort(key=lambda item: item[0], reverse=True)

        used_baseline_ids: set[str] = set()
        used_comparison_ids: set[str] = set()

        for confidence, baseline, comparison, score in candidate_pairs:
            if confidence < self.minimum_match_confidence:
                continue
            if baseline.external_id in used_baseline_ids or comparison.external_id in used_comparison_ids:
                continue

            classification = self.classify(baseline, comparison, score)
            delta_seconds = comparison.duration_seconds - baseline.duration_seconds

            matches.append(
                ActivityMatch(
                    baseline_activity=baseline,
                    comparison_activity=comparison,
                    baseline_source=baseline_source,
                    comparison_source=comparison_source,
                    classification=classification,
                    score=score,
                    confidence=confidence,
                    delta_seconds=delta_seconds,
                    reason=self._build_reason(classification, delta_seconds),
                )
            )

            used_baseline_ids.add(baseline.external_id)
            used_comparison_ids.add(comparison.external_id)

        for baseline in unmatched_baseline:
            if baseline.external_id not in used_baseline_ids:
                matches.append(
                    ActivityMatch(
                        baseline_activity=baseline,
                        comparison_activity=None,
                        baseline_source=baseline_source,
                        comparison_source=comparison_source,
                        classification=MatchClassification.DELETED,
                        score=None,
                        confidence=1.0,
                        delta_seconds=-baseline.duration_seconds,
                        reason=f"{comparison_source.label} version is missing a {baseline_source.label} activity.",
                    )
                )

        for comparison in unmatched_comparison:
            if comparison.external_id not in used_comparison_ids:
                matches.append(
                    ActivityMatch(
                        baseline_activity=None,
                        comparison_activity=comparison,
                        baseline_source=baseline_source,
                        comparison_source=comparison_source,
                        classification=MatchClassification.INSERTED,
                        score=None,
                        confidence=1.0,
                        delta_seconds=comparison.duration_seconds,
                        reason=f"{comparison_source.label} version contains an inserted activity not found in {baseline_source.label}.",
                    )
                )

        return matches

    def score_pair(
        self,
        baseline: ActivitySnapshot,
        comparison: ActivitySnapshot,
    ) -> ActivityMatchScore:
        overlap_score = self._overlap_score(baseline, comparison)
        start_proximity_score = self._time_proximity_score(
            abs((comparison.start_time - baseline.start_time).total_seconds())
        )
        end_proximity_score = 0.0
        if baseline.end_time and comparison.end_time:
            end_proximity_score = self._time_proximity_score(
                abs((comparison.end_time - baseline.end_time).total_seconds())
            )

        duration_similarity_score = self._duration_similarity_score(
            baseline.duration_seconds,
            comparison.duration_seconds,
        )
        activity_type_score = 1.0 if baseline.activity_type_id == comparison.activity_type_id else 0.0

        return ActivityMatchScore(
            overlap_score=overlap_score,
            start_proximity_score=start_proximity_score,
            end_proximity_score=end_proximity_score,
            duration_similarity_score=duration_similarity_score,
            activity_type_score=activity_type_score,
        )

    def classify(
        self,
        baseline: ActivitySnapshot,
        comparison: ActivitySnapshot,
        score: ActivityMatchScore,
    ) -> MatchClassification:
        start_delta = abs((comparison.start_time - baseline.start_time).total_seconds())
        end_delta = 0.0
        if baseline.end_time and comparison.end_time:
            end_delta = abs((comparison.end_time - baseline.end_time).total_seconds())

        duration_delta = comparison.duration_seconds - baseline.duration_seconds

        if baseline.activity_type_id != comparison.activity_type_id and score.overlap_score >= 0.70:
            return MatchClassification.TYPE_CHANGED

        if start_delta <= 60 and end_delta <= 60 and abs(duration_delta) <= 60:
            return MatchClassification.EXACT

        if start_delta > 300 and end_delta > 300 and abs(duration_delta) <= 300:
            return MatchClassification.SHIFTED

        if duration_delta >= 300:
            return MatchClassification.EXTENDED

        if duration_delta <= -300:
            return MatchClassification.SHORTENED

        return MatchClassification.PARTIAL_OVERLAP

    def _overlap_score(self, baseline: ActivitySnapshot, comparison: ActivitySnapshot) -> float:
        if baseline.end_time is None or comparison.end_time is None:
            return 0.0

        overlap_start = max(baseline.start_time, comparison.start_time)
        overlap_end = min(baseline.end_time, comparison.end_time)
        overlap_seconds = max(0, int((overlap_end - overlap_start).total_seconds()))

        union_start = min(baseline.start_time, comparison.start_time)
        union_end = max(baseline.end_time, comparison.end_time)
        union_seconds = max(1, int((union_end - union_start).total_seconds()))

        return round(overlap_seconds / union_seconds, 4)

    def _time_proximity_score(self, delta_seconds: float) -> float:
        if delta_seconds <= 60:
            return 1.0
        if delta_seconds >= 1800:
            return 0.0
        return round(1 - (delta_seconds / 1800), 4)

    def _duration_similarity_score(self, baseline_seconds: int, comparison_seconds: int) -> float:
        largest = max(abs(baseline_seconds), abs(comparison_seconds), 1)
        delta = abs(comparison_seconds - baseline_seconds)
        return round(max(0.0, 1 - (delta / largest)), 4)

    def _build_reason(self, classification: MatchClassification, delta_seconds: int) -> str:
        delta_minutes = round(delta_seconds / 60, 2)

        if classification == MatchClassification.EXACT:
            return "Activity matches baseline with no material difference."
        if classification == MatchClassification.EXTENDED:
            return f"Activity was extended by {delta_minutes} minutes."
        if classification == MatchClassification.SHORTENED:
            return f"Activity was shortened by {abs(delta_minutes)} minutes."
        if classification == MatchClassification.SHIFTED:
            return "Activity appears to be shifted to a different time window."
        if classification == MatchClassification.TYPE_CHANGED:
            return "Activity overlaps baseline but activity type changed."
        return "Activity partially overlaps baseline."
