from dataclasses import dataclass

@dataclass(frozen=True)
class ScanMetrics:
    chunks_total:int
    chunks_completed:int
    chunks_failed:int
    employee_days:int
    findings:int

    @property
    def completion_ratio(self)->float:
        return 1.0 if self.chunks_total==0 else min(1.0,self.chunks_completed/self.chunks_total)
