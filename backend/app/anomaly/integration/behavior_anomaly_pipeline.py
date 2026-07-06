from app.analytics.behavior.domain.profile import BehaviorProfile
from app.anomaly.domain.anomaly_models import AnomalyScore
from app.anomaly.services.anomaly_scorer import AnomalyScorer
from app.anomaly.services.behavior_feature_vector_mapper import BehaviorFeatureVectorMapper


class BehaviorAnomalyPipeline:
    """Scores one behavior profile against peer behavior profiles."""

    def __init__(
        self,
        mapper: BehaviorFeatureVectorMapper | None = None,
        scorer: AnomalyScorer | None = None,
    ) -> None:
        self.mapper = mapper or BehaviorFeatureVectorMapper()
        self.scorer = scorer or AnomalyScorer()

    def score_profile(
        self,
        target_profile: BehaviorProfile,
        peer_profiles: list[BehaviorProfile],
    ) -> AnomalyScore:
        target = self.mapper.from_profile(target_profile)
        peers = [self.mapper.from_profile(profile) for profile in peer_profiles]
        return self.scorer.score(target, peers)
