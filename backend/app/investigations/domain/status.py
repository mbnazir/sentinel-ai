from enum import StrEnum


class InvestigationStatus(StrEnum):
    NEW = "new"
    TRIAGED = "triaged"
    ASSIGNED = "assigned"
    IN_REVIEW = "in_review"
    NEEDS_MORE_INFO = "needs_more_info"
    SUBSTANTIATED = "substantiated"
    UNSUBSTANTIATED = "unsubstantiated"
    CLOSED = "closed"


ALLOWED_TRANSITIONS: dict[InvestigationStatus, set[InvestigationStatus]] = {
    InvestigationStatus.NEW: {InvestigationStatus.TRIAGED, InvestigationStatus.ASSIGNED, InvestigationStatus.CLOSED},
    InvestigationStatus.TRIAGED: {InvestigationStatus.ASSIGNED, InvestigationStatus.IN_REVIEW, InvestigationStatus.CLOSED},
    InvestigationStatus.ASSIGNED: {InvestigationStatus.IN_REVIEW, InvestigationStatus.NEEDS_MORE_INFO, InvestigationStatus.CLOSED},
    InvestigationStatus.IN_REVIEW: {
        InvestigationStatus.NEEDS_MORE_INFO,
        InvestigationStatus.SUBSTANTIATED,
        InvestigationStatus.UNSUBSTANTIATED,
        InvestigationStatus.CLOSED,
    },
    InvestigationStatus.NEEDS_MORE_INFO: {InvestigationStatus.IN_REVIEW, InvestigationStatus.CLOSED},
    InvestigationStatus.SUBSTANTIATED: {InvestigationStatus.CLOSED},
    InvestigationStatus.UNSUBSTANTIATED: {InvestigationStatus.CLOSED},
    InvestigationStatus.CLOSED: set(),
}


def can_transition(current: InvestigationStatus, target: InvestigationStatus) -> bool:
    return target in ALLOWED_TRANSITIONS[current]
