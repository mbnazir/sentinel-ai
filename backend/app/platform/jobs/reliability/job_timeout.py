from dataclasses import dataclass


@dataclass(frozen=True)
class JobTimeoutPolicy:
    default_timeout_seconds: int = 1800

    def timeout_for(self, job_type: str) -> int:
        return {
            "quartz_sync": 3600,
            "scan_run": 7200,
            "behavior_refresh": 3600,
            "anomaly_score": 3600,
            "anomaly_case_attachment": 1800,
        }.get(job_type, self.default_timeout_seconds)
