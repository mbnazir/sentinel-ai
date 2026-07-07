from dataclasses import dataclass


@dataclass(frozen=True)
class RetryDecision:
    should_retry: bool
    delay_seconds: int
    reason: str


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: int = 60
    max_delay_seconds: int = 3600
    backoff_multiplier: int = 2

    def evaluate(self, attempt_count: int) -> RetryDecision:
        if attempt_count >= self.max_attempts:
            return RetryDecision(
                should_retry=False,
                delay_seconds=0,
                reason=f"max attempts reached ({attempt_count}/{self.max_attempts})",
            )

        delay = min(
            self.max_delay_seconds,
            self.base_delay_seconds * (self.backoff_multiplier ** max(0, attempt_count - 1)),
        )
        return RetryDecision(
            should_retry=True,
            delay_seconds=delay,
            reason=f"retry scheduled after {delay} seconds",
        )
