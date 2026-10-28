from enum import IntEnum


class ActivityDataSource(IntEnum):
    PHONE = 0
    SYSTEM = 1
    AGENT = 2
    SUPERVISOR = 3
    MANAGER = 4
    PAYROLL = 5

    @property
    def label(self) -> str:
        return self.name.title()

    @property
    def is_manual(self) -> bool:
        return self.value >= ActivityDataSource.AGENT
