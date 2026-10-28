from app.application.connector_contract import WorkforceConnector
from app.connectors.quartz import QuartzConnectorConfig, QuartzRestConnector
from app.core.config import settings
from app.infrastructure.models import ConnectorModel


class UnsupportedConnectorError(ValueError):
    pass


def build_connector(row: ConnectorModel) -> WorkforceConnector:
    if row.connector_type == "quartz" and row.mode == "rest-api":
        if not row.base_url:
            raise UnsupportedConnectorError("Quartz REST connector requires base_url")
        config = row.config_json or {}
        return QuartzRestConnector(
            QuartzConnectorConfig(
                base_url=row.base_url,
                bearer_token=settings.quartz_api_bearer_token,
                sessions_path=str(config.get("sessions_path", "/api/sentinel/v1/login-sessions")),
                activities_path=str(config.get("activities_path", "/api/sentinel/v1/activities")),
                timeout_seconds=float(config.get("timeout_seconds", 30.0)),
                page_size=int(config.get("page_size", 500)),
                activity_session_id_batch_size=int(config.get("activity_session_id_batch_size", 25)),
                request_max_attempts=int(config.get("request_max_attempts", 4)),
                retry_backoff_base_seconds=float(config.get("retry_backoff_base_seconds", 0.5)),
                retry_backoff_max_seconds=float(config.get("retry_backoff_max_seconds", 20.0)),
                verify_tls=bool(config.get("verify_tls", True)),
            )
        )
    raise UnsupportedConnectorError(
        f"unsupported connector {row.connector_type}/{row.mode}"
    )
