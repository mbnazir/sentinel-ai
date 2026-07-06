from datetime import date

from sqlalchemy.orm import Session

from app.infrastructure.persistence.models_normalized import NormalizedActivityModel, NormalizedLoginSessionModel


class NormalizedScanRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_sessions_for_shift_range(
        self,
        organization_id: str,
        shift_date_from: date,
        shift_date_to: date,
    ) -> list[NormalizedLoginSessionModel]:
        return (
            self.session.query(NormalizedLoginSessionModel)
            .filter(NormalizedLoginSessionModel.organization_id == organization_id)
            .filter(NormalizedLoginSessionModel.shift_date >= shift_date_from)
            .filter(NormalizedLoginSessionModel.shift_date <= shift_date_to)
            .order_by(NormalizedLoginSessionModel.shift_date, NormalizedLoginSessionModel.external_id)
            .all()
        )

    def list_activities_for_session(
        self,
        organization_id: str,
        login_session_external_id: str,
    ) -> list[NormalizedActivityModel]:
        return (
            self.session.query(NormalizedActivityModel)
            .filter_by(
                organization_id=organization_id,
                login_session_external_id=login_session_external_id,
            )
            .order_by(NormalizedActivityModel.source, NormalizedActivityModel.start_time)
            .all()
        )
