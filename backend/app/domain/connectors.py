from dataclasses import dataclass
from enum import StrEnum


class ConnectorType(StrEnum):
    QUARTZ = "quartz"
    CSV = "csv"
    REST = "rest"


class ConnectorMode(StrEnum):
    REST_API = "rest-api"
    READ_ONLY_DATABASE = "read-only-database"
    FILE_IMPORT = "file-import"


@dataclass(frozen=True, slots=True)
class ConnectorDefinition:
    name: str
    connector_type: ConnectorType
    mode: ConnectorMode
    enabled: bool = True
