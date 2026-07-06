from app.anomaly.services.robust_statistics import RobustStatistics


def test_robust_z_score_flags_large_outlier() -> None:
    stats = RobustStatistics()

    z_score = stats.robust_z_score(100, [10, 11, 9, 10, 12])

    assert z_score > 2.5


def test_robust_z_score_handles_no_variance() -> None:
    stats = RobustStatistics()

    assert stats.robust_z_score(10, [10, 10, 10]) == 0.0
    assert stats.robust_z_score(20, [10, 10, 10]) == 10.0
