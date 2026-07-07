from app.platform.jobs.reliability.retry_policy import RetryPolicy


def test_retry_policy_allows_retry_before_max_attempts() -> None:
    decision = RetryPolicy(max_attempts=3, base_delay_seconds=10).evaluate(1)

    assert decision.should_retry is True
    assert decision.delay_seconds == 10


def test_retry_policy_stops_at_max_attempts() -> None:
    decision = RetryPolicy(max_attempts=3).evaluate(3)

    assert decision.should_retry is False
