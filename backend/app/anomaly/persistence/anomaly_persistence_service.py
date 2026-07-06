from datetime import date

from app.analytics.behavior.domain.profile import BehaviorProfile
from app.anomaly.domain.anomaly_models import AnomalyScore
from app.anomaly.integration.behavior_anomaly_pipeline import BehaviorAnomalyPipeline
from app.anomaly.persistence.anomaly_finding_repository import AnomalyFindingRepository


class AnomalyPersistenceService:
    def __init__(
        self,
        repository: AnomalyFindingRepository,
        pipeline: BehaviorAnomalyPipeline | None = None,
    ) -> None:
        self.repository = repository
        self.pipeline = pipeline or BehaviorAnomalyPipeline()

    def score_and_persist_profile(
        self,
        organization_id: str,
        target_profile: BehaviorProfile,
        peer_profiles: list[BehaviorProfile],
        as_of_date: date,
    ) -> AnomalyScore:
        result = self.pipeline.score_profile(target_profile, peer_profiles)
        return self.repository.save(
            organization_id=organization_id,
            anomaly_score=result,
            window_days=target_profile.window_days,
            as_of_date=as_of_date,
        )
