from enum import Enum


class DataSource(str, Enum):
    PHONE = "phone"
    SYSTEM = "system"
    AGENT = "agent"
    SUPERVISOR = "supervisor"
    MANAGER = "manager"
    PAYROLL = "payroll"
    UNKNOWN = "unknown"


QUARTZ_DATA_SOURCE_MAP = {
    0: DataSource.PHONE,
    1: DataSource.SYSTEM,
    2: DataSource.AGENT,
    3: DataSource.SUPERVISOR,
    4: DataSource.MANAGER,
    5: DataSource.PAYROLL,
}


def map_quartz_data_source(data_source_id: int | None) -> DataSource:
    if data_source_id is None:
        return DataSource.UNKNOWN
    return QUARTZ_DATA_SOURCE_MAP.get(data_source_id, DataSource.UNKNOWN)
