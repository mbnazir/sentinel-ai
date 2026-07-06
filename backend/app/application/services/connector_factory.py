from typing import Any

from app.application.interfaces.connector import Connector
from app.connectors.quartz.config import QuartzConnectorConfig
from app.connectors.quartz.connector import QuartzConnector
from app.core.exceptions.exceptions import ValidationError


class ConnectorFactory:
    def create(self, connector_type: str, configuration: dict[str, Any]) -> Connector:
        if connector_type == "quartz":
            return QuartzConnector(QuartzConnectorConfig(**configuration))
        raise ValidationError(f"Unsupported connector type: {connector_type}")
