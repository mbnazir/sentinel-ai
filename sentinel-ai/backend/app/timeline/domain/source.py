from enum import IntEnum

class DataSource(IntEnum):
    PHONE = 0
    SYSTEM = 1
    AGENT = 2
    SUPERVISOR = 3
    MANAGER = 4
    PAYROLL = 5

    @property
    def label(self) -> str:
        return {
            DataSource.PHONE: "Phone",
            DataSource.SYSTEM: "System",
            DataSource.AGENT: "Agent",
            DataSource.SUPERVISOR: "Supervisor",
            DataSource.MANAGER: "Manager",
            DataSource.PAYROLL: "Payroll",
        }[self]
