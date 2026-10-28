from datetime import date
from uuid import uuid4

from app.investigations.hashing import immutable_finding_hash
from app.investigations.models import CaseStatus
from app.investigations.workflow import can_transition


def test_finding_hash_is_stable_and_sensitive():
    a = {"rule_id": "SA-R001", "agent_id": "A1", "shift_date": "2026-08-27", "risk": 22.0}
    b = dict(a)
    assert immutable_finding_hash(a) == immutable_finding_hash(dict(a))
    b["risk"] = 23.0
    assert immutable_finding_hash(a) != immutable_finding_hash(b)


def test_case_workflow_allows_normal_review_path():
    assert can_transition(CaseStatus.OPEN, CaseStatus.IN_REVIEW)
    assert can_transition(CaseStatus.IN_REVIEW, CaseStatus.AWAITING_INFO)
    assert can_transition(CaseStatus.AWAITING_INFO, CaseStatus.IN_REVIEW)
    assert can_transition(CaseStatus.IN_REVIEW, CaseStatus.RESOLVED)
    assert can_transition(CaseStatus.RESOLVED, CaseStatus.CLOSED)


def test_closed_case_cannot_be_reopened_by_workflow():
    assert not can_transition(CaseStatus.CLOSED, CaseStatus.IN_REVIEW)


def test_case_status_can_remain_unchanged():
    assert can_transition(CaseStatus.OPEN, CaseStatus.OPEN)
