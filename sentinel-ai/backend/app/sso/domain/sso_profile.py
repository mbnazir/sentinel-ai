from dataclasses import dataclass


@dataclass(frozen=True)
class SSOProfile:
    provider: str
    subject: str
    email: str
    full_name: str
    organization_id: str
    groups: list[str]
