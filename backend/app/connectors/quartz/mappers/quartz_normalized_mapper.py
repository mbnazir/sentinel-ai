from app.connectors.quartz.client.quartz_api_models import QuartzActivityDTO, QuartzSessionDTO
from app.domain.entities.activity import Activity
from app.domain.entities.login_session import LoginSession


class QuartzNormalizedMapper:
    def session_to_domain(self, dto: QuartzSessionDTO) -> LoginSession:
        return LoginSession(
            external_id=dto.id,
            agent_external_id=dto.agent_id,
            supervisor_external_id=dto.supervisor_id,
            shift_date=dto.shift_date,
            start_time=dto.start_date,
            end_time=dto.end_date,
            status=str(dto.status_id) if dto.status_id is not None else None,
        )

    def activity_to_domain(self, dto: QuartzActivityDTO) -> Activity:
        return Activity(
            external_id=dto.id,
            login_session_external_id=dto.login_session_id,
            agent_external_id=dto.agent_id,
            source=self._source_label(dto.data_source_id),
            activity_type=str(dto.activity_type_id),
            start_time=dto.start_time,
            end_time=dto.end_time,
            duration_seconds=dto.duration_seconds,
            comment=dto.comment,
        )

    def _source_label(self, data_source_id: int) -> str:
        return {
            0: "Phone",
            1: "System",
            2: "Agent",
            3: "Supervisor",
            4: "Manager",
            5: "Payroll",
        }.get(data_source_id, "Unknown")
