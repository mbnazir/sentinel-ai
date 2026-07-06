from datetime import date

from app.anomaly.domain.anomaly_models import AnomalyScore, AnomalySeverity
from app.anomaly.persistence.anomaly_persistence_service import AnomalyPersistenceService


class FakeRepository:
    def __init__(self) -> None:
        self.saved = None

    def save(self, organization_id, anomaly_score, window_days, as_of_date):
        self.saved = (organization_id, anomaly_score, window_days, as_of_date)
        return anomaly_score


class FakePipeline:
    def score_profile(self, target_profile, peer_profiles):
        return AnomalyScore("agent", "A1", 50, AnomalySeverity.MEDIUM, [], "Medium anomaly.")


class FakeProfile:
    entity_type = "agent"
    entity_id = "A1"
    window_days = 90


def test_persistence_service_scores_and_saves() -> None:
    repository = FakeRepository()
    service = AnomalyPersistenceService(repository, FakePipeline())

    result = service.score_and_persist_profile("ORG1", FakeProfile(), [], date(2026, 7, 1))

    assert result.score == 50
    assert repository.saved[0] == "ORG1"
    assert repository.saved[2] == 90
