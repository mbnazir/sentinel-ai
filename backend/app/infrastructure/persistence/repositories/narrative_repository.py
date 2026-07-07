from sqlalchemy.orm import Session
from app.ai.domain.investigation_narrative import InvestigationNarrative
from app.infrastructure.persistence.models_investigations import InvestigationNarrativeModel

class NarrativeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, narrative: InvestigationNarrative) -> InvestigationNarrative:
        self.session.add(InvestigationNarrativeModel(
            case_id=narrative.case_id,
            executive_summary=narrative.executive_summary,
            key_findings=narrative.key_findings,
            evidence_summary=narrative.evidence_summary,
            recommended_next_steps=narrative.recommended_next_steps,
            limitations=narrative.limitations,
            raw_model_output=narrative.raw_model_output,
        ))
        self.session.commit()
        return narrative

    def latest_for_case(self, case_id: str) -> InvestigationNarrative | None:
        model = self.session.query(InvestigationNarrativeModel).filter_by(case_id=case_id).order_by(InvestigationNarrativeModel.created_at.desc()).first()
        if model is None:
            return None
        return InvestigationNarrative(case_id=model.case_id, executive_summary=model.executive_summary, key_findings=list(model.key_findings), evidence_summary=list(model.evidence_summary), recommended_next_steps=list(model.recommended_next_steps), limitations=list(model.limitations), raw_model_output=model.raw_model_output)
