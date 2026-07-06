from app.anomaly.domain.anomaly_models import FeatureVector


class BehaviorFeatureVectorMapper:
    """Maps behavior profiles or API payloads into anomaly feature vectors."""

    def from_profile(self, profile) -> FeatureVector:
        feature_map = {}

        for metric in getattr(profile, "metrics", []):
            feature_map[getattr(metric, "name")] = float(getattr(metric, "value"))

        return FeatureVector(
            entity_type=getattr(profile, "entity_type"),
            entity_id=getattr(profile, "entity_id"),
            features=feature_map,
        )

    def from_dict(self, payload: dict) -> FeatureVector:
        metrics = payload.get("metrics", [])
        return FeatureVector(
            entity_type=str(payload["entity_type"]),
            entity_id=str(payload["entity_id"]),
            features={str(item["name"]): float(item["value"]) for item in metrics},
        )
