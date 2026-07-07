from app.analytics.behavior.domain.metric import TrendDirection
from app.analytics.behavior.services.trend_detection_service import TrendDetectionService


def test_detects_increasing_trend() -> None:
    result = TrendDetectionService().detect("risk", [10, 20, 30, 40])
    assert result.direction == TrendDirection.INCREASING
    assert result.slope > 0


def test_detects_decreasing_trend() -> None:
    result = TrendDetectionService().detect("risk", [40, 30, 20, 10])
    assert result.direction == TrendDirection.DECREASING
    assert result.slope < 0


def test_detects_insufficient_data() -> None:
    result = TrendDetectionService().detect("risk", [10])
    assert result.direction == TrendDirection.INSUFFICIENT_DATA
