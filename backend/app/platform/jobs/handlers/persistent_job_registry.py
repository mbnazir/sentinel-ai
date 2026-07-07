from app.platform.jobs.handlers.anomaly_case_attachment_handler import AnomalyCaseAttachmentJobHandler
from app.platform.jobs.handlers.quartz_sync_handler import QuartzSyncJobHandler
from app.platform.jobs.handlers.scan_run_handler import ScanRunJobHandler
from app.platform.jobs.job_handlers import NoOpJobHandler
from app.platform.jobs.job_models import JobType
from app.platform.jobs.job_registry import JobHandlerRegistry


def build_persistent_job_registry(session) -> JobHandlerRegistry:
    registry = JobHandlerRegistry()

    registry.register(QuartzSyncJobHandler(session))
    registry.register(ScanRunJobHandler(session))
    registry.register(AnomalyCaseAttachmentJobHandler(session))

    # Still scaffolded for later implementation.
    registry.register(NoOpJobHandler(JobType.BEHAVIOR_REFRESH))
    registry.register(NoOpJobHandler(JobType.ANOMALY_SCORE))

    return registry
