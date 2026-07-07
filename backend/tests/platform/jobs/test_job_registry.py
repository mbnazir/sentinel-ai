from app.platform.jobs.job_models import JobType
from app.platform.jobs.job_registry import build_default_job_registry


def test_default_registry_contains_all_job_types() -> None:
    registry = build_default_job_registry()

    for job_type in JobType:
        assert registry.get(job_type).job_type == job_type
