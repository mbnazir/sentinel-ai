from datetime import date

from app.analytics.behavior.domain.session_fact import SessionRiskFact
from app.analytics.behavior.services.behavior_intelligence_service import BehaviorIntelligenceService


class MemoryBehaviorRepository:
    def __init__(self) -> None:
        self.profiles = []
        self.deviations = []

    def save_profile(self, organization_id, profile):
        self.profiles.append((organization_id, profile))
        return profile

    def save_deviation(self, organization_id, entity_type, window_days, as_of_date, deviation):
        self.deviations.append((organization_id, entity_type, window_days, as_of_date, deviation))
        return deviation


def test_refresh_agent_profiles_persists_profiles_and_deviations() -> None:
    repository = MemoryBehaviorRepository()
    service = BehaviorIntelligenceService(repository)

    facts = [
        SessionRiskFact("LS1", "A1", "S1", None, None, None, date(2026, 7, 1), 80, manual_added_seconds=3600, rule_count=3),
        SessionRiskFact("LS2", "A2", "S1", None, None, None, date(2026, 7, 1), 20, manual_added_seconds=0, rule_count=1),
        SessionRiskFact("LS3", "A1", "S1", None, None, None, date(2026, 7, 2), 90, manual_added_seconds=1800, rule_count=2),
    ]

    profiles = service.refresh_agent_profiles("ORG1", facts, date(2026, 7, 3), 30)

    assert len(profiles) == 2
    assert len(repository.profiles) == 2
    assert len(repository.deviations) == 4
    assert max(profile.behavior_score for profile in profiles) > 0
