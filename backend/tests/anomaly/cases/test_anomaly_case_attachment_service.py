from app.anomaly.cases.anomaly_case_attachment_service import AnomalyCaseAttachmentService
from app.anomaly.domain.anomaly_models import AnomalyScore, AnomalySeverity, FeatureAnomaly


class MemoryInvestigationRepository:
    def __init__(self) -> None:
        self.cases = []

    def list(self, organization_id=None, limit=500):
        return self.cases

    def save(self, case):
        existing = [item for item in self.cases if item.case_id == case.case_id]
        if not existing:
            self.cases.append(case)
        else:
            index = self.cases.index(existing[0])
            self.cases[index] = case
        return case


class FixedCaseIdGenerator:
    def generate(self):
        return "CASE-1"


def anomaly(score=85):
    return AnomalyScore(
        entity_type="agent",
        entity_id="A1",
        score=score,
        severity=AnomalySeverity.CRITICAL,
        anomalies=[FeatureAnomaly("average_risk_score", 90, 20, 7.5, 20, "Risk outlier.")],
        summary="Critical anomaly.",
    )


def test_attachment_service_creates_case() -> None:
    repository = MemoryInvestigationRepository()
    service = AnomalyCaseAttachmentService(repository, case_id_generator=FixedCaseIdGenerator())

    case = service.attach_or_create_case("ORG1", anomaly())

    assert case is not None
    assert case.case_id == "CASE-1"
    assert case.evidence_links


def test_attachment_service_reuses_open_case() -> None:
    repository = MemoryInvestigationRepository()
    service = AnomalyCaseAttachmentService(repository, case_id_generator=FixedCaseIdGenerator())

    first = service.attach_or_create_case("ORG1", anomaly())
    second = service.attach_or_create_case("ORG1", anomaly(90))

    assert first.case_id == second.case_id
    assert second.risk_score == 90
    assert len(repository.cases) == 1
