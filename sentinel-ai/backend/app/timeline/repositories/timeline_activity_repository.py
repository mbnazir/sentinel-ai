from sqlalchemy.orm import Session

from app.infrastructure.persistence.models_timeline import NormalizedTimelineActivityModel


class TimelineActivityRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_by_login_session(
        self,
        login_session_external_id: str,
    ) -> list[NormalizedTimelineActivityModel]:
        return (
            self.session.query(NormalizedTimelineActivityModel)
            .filter_by(login_session_external_id=login_session_external_id)
            .order_by(
                NormalizedTimelineActivityModel.data_source_id,
                NormalizedTimelineActivityModel.start_time,
            )
            .all()
        )
