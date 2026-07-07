from app.platform.jobs.reliability.job_lease import InMemoryJobLeaseRepository


def test_lease_prevents_duplicate_acquire() -> None:
    repo = InMemoryJobLeaseRepository()

    first = repo.acquire("JOB1", "W1")
    second = repo.acquire("JOB1", "W2")

    assert first is not None
    assert second is None


def test_release_requires_same_worker() -> None:
    repo = InMemoryJobLeaseRepository()
    repo.acquire("JOB1", "W1")

    assert repo.release("JOB1", "W2") is False
    assert repo.release("JOB1", "W1") is True
