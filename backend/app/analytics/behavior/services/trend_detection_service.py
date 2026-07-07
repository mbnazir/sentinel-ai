from app.analytics.behavior.domain.metric import TrendDirection, TrendResult


class TrendDetectionService:
    """Simple slope-based trend detector.

    This is intentionally deterministic and dependency-light. Later milestones can replace
    or augment this with statsmodels/scikit-learn without changing callers.
    """

    def detect(self, metric_name: str, values: list[float]) -> TrendResult:
        if len(values) < 2:
            first = values[0] if values else 0.0
            return TrendResult(
                metric_name=metric_name,
                direction=TrendDirection.INSUFFICIENT_DATA,
                slope=0.0,
                first_value=first,
                last_value=first,
                change_percent=0.0,
            )

        n = len(values)
        x_values = list(range(n))
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values, strict=True))
        denominator = sum((x - x_mean) ** 2 for x in x_values) or 1.0
        slope = numerator / denominator

        first = values[0]
        last = values[-1]
        change_percent = 0.0 if first == 0 else round(((last - first) / abs(first)) * 100, 2)

        if abs(slope) < 0.05:
            direction = TrendDirection.STABLE
        elif slope > 0:
            direction = TrendDirection.INCREASING
        else:
            direction = TrendDirection.DECREASING

        return TrendResult(
            metric_name=metric_name,
            direction=direction,
            slope=round(slope, 4),
            first_value=first,
            last_value=last,
            change_percent=change_percent,
        )
