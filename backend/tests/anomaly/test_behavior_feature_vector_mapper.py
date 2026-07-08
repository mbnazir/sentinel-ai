from app.anomaly.services.behavior_feature_vector_mapper import BehaviorFeatureVectorMapper


def test_mapper_from_dict() -> None:
    vector = BehaviorFeatureVectorMapper().from_dict(
        {
            "entity_type": "agent",
            "entity_id": "A1",
            "metrics": [
                {"name": "average_risk_score", "value": 80},
                {"name": "manual_added_minutes", "value": 120},
            ],
        }
    )

    assert vector.entity_type == "agent"
    assert vector.entity_id == "A1"
    assert vector.features["manual_added_minutes"] == 120
