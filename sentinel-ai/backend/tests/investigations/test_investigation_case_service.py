from app.investigations.domain.status import InvestigationStatus
from app.investigations.services.case_id_generator import CaseIdGenerator
from app.investigations.services.investigation_case_service import (
    InvalidInvestigationTransitionError,
    InvestigationCaseService,
)
from app.rules.domain.evidence import Evidence
from app.rules.domain.rule_result import RuleResult
from app.rules.domain.severity import Severity
from app.scoring.domain.risk_assessment import RiskAssessment
from app.scoring.domain.risk_level import RiskLevel


class FixedCaseIdGenerator(CaseIdGenerator):
    def generate(self) -> str:
        return "SEN-TEST-0001"


def assessment() -> RiskAssessment:
    rule = RuleResult(
        rule_id="R1",
        rule_name="Inserted Activity",
        severity=Severity.HIGH,
        score=50,
        reason="Agent inserted activity.",
        evidence=[Evidence("inserted_activity", {"activity_id": "A1"})],
    )
    return RiskAssessment(
        entity_type="login_session",
        entity_id="LS-1",
        risk_score=85,
        risk_level=RiskLevel.CRITICAL,
        summary="Critical session risk.",
        rule_results=[rule],
        top_reasons=["Agent inserted activity."],
    )


def test_create_case_from_risk_assessment() -> None:
    service = InvestigationCaseService(FixedCaseIdGenerator())

    case = service.create_from_risk_assessment("ORG-1", assessment())

    assert case.case_id == "SEN-TEST-0001"
    assert case.priority.value == "critical"
    assert case.status == InvestigationStatus.NEW
    assert len(case.evidence_links) == 1


def test_assign_case_sets_assignee_and_status() -> None:
    service = InvestigationCaseService(FixedCaseIdGenerator())
    case = service.create_from_risk_assessment("ORG-1", assessment())

    assigned = service.assign(case, "U-1")

    assert assigned.assigned_to == "U-1"
    assert assigned.status == InvestigationStatus.ASSIGNED


def test_valid_transition() -> None:
    service = InvestigationCaseService(FixedCaseIdGenerator())
    case = service.create_from_risk_assessment("ORG-1", assessment())

    triaged = service.transition(case, InvestigationStatus.TRIAGED)

    assert triaged.status == InvestigationStatus.TRIAGED


def test_invalid_transition_raises() -> None:
    service = InvestigationCaseService(FixedCaseIdGenerator())
    case = service.create_from_risk_assessment("ORG-1", assessment())

    try:
        service.transition(case, InvestigationStatus.SUBSTANTIATED)
    except InvalidInvestigationTransitionError:
        assert True
    else:
        assert False, "Expected invalid transition error"


def test_add_comment() -> None:
    service = InvestigationCaseService(FixedCaseIdGenerator())
    case = service.create_from_risk_assessment("ORG-1", assessment())

    updated = service.add_comment(case, "U-1", "Reviewed with supervisor.")

    assert len(updated.comments) == 1
    assert updated.comments[0].body == "Reviewed with supervisor."
