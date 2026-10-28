from decimal import Decimal
from collections.abc import Iterable

from app.weekly.models import WeeklyAdjustment, WeeklyPayableSummary

THRESHOLD_SECONDS = Decimal(144000)


def calculate_overtime(*, employee_id: str, week_start, week_end,
                       baseline_eligible_seconds: Decimal | None,
                       final_eligible_seconds: Decimal | None,
                       adjustments: Iterable[WeeklyAdjustment] = (), status="PROVISIONAL",
                       threshold_seconds: Decimal = THRESHOLD_SECONDS) -> WeeklyPayableSummary:
    from app.weekly.models import ResolutionStatus
    baseline = baseline_eligible_seconds
    final = final_eligible_seconds
    state = ResolutionStatus(status)
    if baseline is None or final is None:
        return WeeklyPayableSummary(employee_id=employee_id, week_start=week_start, week_end=week_end,
                                    status=ResolutionStatus.INSUFFICIENT_DATA,
                                    adjustments=tuple(adjustments))
    baseline_ot = max(Decimal(0), baseline - threshold_seconds)
    final_ot = max(Decimal(0), final - threshold_seconds)
    incremental = max(Decimal(0), final_ot - baseline_ot)
    added = max(Decimal(0), final - baseline)
    return WeeklyPayableSummary(employee_id=employee_id, week_start=week_start, week_end=week_end,
                                baseline_eligible_seconds=baseline, final_eligible_seconds=final,
                                baseline_overtime_seconds=baseline_ot, final_overtime_seconds=final_ot,
                                incremental_overtime_seconds=incremental,
                                additional_regular_seconds=max(Decimal(0), added-incremental),
                                status=state, adjustments=tuple(adjustments))
