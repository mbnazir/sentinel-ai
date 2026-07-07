from app.analytics.behavior.services.peer_comparison_service import PeerComparisonService


def test_peer_comparison_flags_outlier() -> None:
    result = PeerComparisonService().compare(
        entity_id="A1",
        metric_name="manual_added_minutes",
        entity_value=100,
        peer_values=[10, 12, 11, 9, 10],
        z_threshold=2.0,
    )
    assert result.is_outlier is True
    assert result.z_score > 2


def test_peer_comparison_handles_empty_peers() -> None:
    result = PeerComparisonService().compare("A1", "risk", 10, [])
    assert result.peer_average == 0
    assert result.is_outlier is False
