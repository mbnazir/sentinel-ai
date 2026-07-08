from app.investigations.domain.status import InvestigationStatus, can_transition


def test_allowed_transition() -> None:
    assert can_transition(InvestigationStatus.NEW, InvestigationStatus.TRIAGED) is True


def test_disallowed_transition() -> None:
    assert can_transition(InvestigationStatus.NEW, InvestigationStatus.SUBSTANTIATED) is False


def test_closed_has_no_transitions() -> None:
    assert can_transition(InvestigationStatus.CLOSED, InvestigationStatus.IN_REVIEW) is False
