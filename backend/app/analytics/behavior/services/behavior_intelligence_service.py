from datetime import date

from app.analytics.behavior.domain.profile import BehaviorProfile
from app.analytics.behavior.domain.session_fact import SessionRiskFact
from app.analytics.behavior.persistence.behavior_repository import BehaviorRepository
from app.analytics.behavior.services.behavior_aggregation_service import BehaviorAggregationService
from app.analytics.behavior.services.peer_comparison_service import PeerComparisonService


class BehaviorIntelligenceService:
    """Persistent behavior intelligence orchestration.

    Produces rolling profiles and peer deviations for entities.
    """

    def __init__(
        self,
        repository: BehaviorRepository,
        aggregation_service: BehaviorAggregationService | None = None,
        peer_service: PeerComparisonService | None = None,
    ) -> None:
        self.repository = repository
        self.aggregation_service = aggregation_service or BehaviorAggregationService()
        self.peer_service = peer_service or PeerComparisonService()

    def refresh_agent_profiles(
        self,
        organization_id: str,
        facts: list[SessionRiskFact],
        as_of_date: date,
        window_days: int = 90,
    ) -> list[BehaviorProfile]:
        agent_ids = sorted({fact.agent_external_id for fact in facts if fact.agent_external_id})
        profiles = []

        for agent_id in agent_ids:
            profile = self.aggregation_service.build_agent_profile(
                agent_external_id=agent_id,
                facts=facts,
                date_to=as_of_date,
                window_days=window_days,
            )
            profiles.append(self.repository.save_profile(organization_id, profile))

        self._persist_peer_deviations(
            organization_id=organization_id,
            entity_type="agent",
            profiles=profiles,
            as_of_date=as_of_date,
            window_days=window_days,
            metric_name="manual_added_minutes",
        )
        self._persist_peer_deviations(
            organization_id=organization_id,
            entity_type="agent",
            profiles=profiles,
            as_of_date=as_of_date,
            window_days=window_days,
            metric_name="average_risk_score",
        )

        return profiles

    def refresh_supervisor_profiles(
        self,
        organization_id: str,
        facts: list[SessionRiskFact],
        as_of_date: date,
        window_days: int = 90,
    ) -> list[BehaviorProfile]:
        supervisor_ids = sorted({fact.supervisor_external_id for fact in facts if fact.supervisor_external_id})
        profiles = []

        for supervisor_id in supervisor_ids:
            profile = self.aggregation_service.build_supervisor_profile(
                supervisor_external_id=supervisor_id,
                facts=facts,
                date_to=as_of_date,
                window_days=window_days,
            )
            profiles.append(self.repository.save_profile(organization_id, profile))

        self._persist_peer_deviations(
            organization_id=organization_id,
            entity_type="supervisor",
            profiles=profiles,
            as_of_date=as_of_date,
            window_days=window_days,
            metric_name="average_risk_score",
        )

        return profiles

    def _persist_peer_deviations(
        self,
        organization_id: str,
        entity_type: str,
        profiles: list[BehaviorProfile],
        as_of_date: date,
        window_days: int,
        metric_name: str,
    ) -> None:
        values_by_entity = {
            profile.entity_id: self._metric_value(profile, metric_name)
            for profile in profiles
        }

        for entity_id, entity_value in values_by_entity.items():
            peer_values = [
                value
                for peer_entity_id, value in values_by_entity.items()
                if peer_entity_id != entity_id
            ]
            deviation = self.peer_service.compare(
                entity_id=entity_id,
                metric_name=metric_name,
                entity_value=entity_value,
                peer_values=peer_values,
            )
            self.repository.save_deviation(
                organization_id=organization_id,
                entity_type=entity_type,
                window_days=window_days,
                as_of_date=as_of_date,
                deviation=deviation,
            )

    def _metric_value(self, profile: BehaviorProfile, metric_name: str) -> float:
        for metric in profile.metrics:
            if metric.name == metric_name:
                return float(metric.value)
        return 0.0
