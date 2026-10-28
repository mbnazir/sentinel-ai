from app.investigations.models import CaseStatus

_ALLOWED: dict[CaseStatus, set[CaseStatus]] = {
    CaseStatus.OPEN: {CaseStatus.IN_REVIEW, CaseStatus.CLOSED},
    CaseStatus.IN_REVIEW: {CaseStatus.AWAITING_INFO, CaseStatus.RESOLVED, CaseStatus.CLOSED},
    CaseStatus.AWAITING_INFO: {CaseStatus.IN_REVIEW, CaseStatus.CLOSED},
    CaseStatus.RESOLVED: {CaseStatus.CLOSED, CaseStatus.IN_REVIEW},
    CaseStatus.CLOSED: set(),
}


def can_transition(current: CaseStatus, target: CaseStatus) -> bool:
    return target == current or target in _ALLOWED[current]
