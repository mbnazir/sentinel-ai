from statistics import median


class RobustStatistics:
    """Dependency-free robust statistics helper using median and MAD."""

    def median(self, values: list[float]) -> float:
        if not values:
            return 0.0
        return float(median(values))

    def mad(self, values: list[float]) -> float:
        if not values:
            return 0.0
        center = self.median(values)
        deviations = [abs(value - center) for value in values]
        return float(median(deviations)) if deviations else 0.0

    def robust_z_score(self, value: float, values: list[float]) -> float:
        center = self.median(values)
        mad = self.mad(values)

        if mad == 0:
            return 0.0 if value == center else 10.0

        return round(0.6745 * (value - center) / mad, 4)
