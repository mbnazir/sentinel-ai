from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    INVESTIGATOR = "investigator"
    COMPLIANCE = "compliance"
    SUPERVISOR = "supervisor"
    READ_ONLY = "read_only"


class Permission(StrEnum):
    VIEW_DASHBOARD = "view_dashboard"
    VIEW_CASES = "view_cases"
    MANAGE_CASES = "manage_cases"
    ASSIGN_CASES = "assign_cases"
    CLOSE_CASES = "close_cases"
    GENERATE_AI_NARRATIVE = "generate_ai_narrative"
    MANAGE_CONNECTORS = "manage_connectors"
    MANAGE_USERS = "manage_users"


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.ADMIN: set(Permission),
    Role.COMPLIANCE: {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_CASES,
        Permission.MANAGE_CASES,
        Permission.ASSIGN_CASES,
        Permission.CLOSE_CASES,
        Permission.GENERATE_AI_NARRATIVE,
    },
    Role.INVESTIGATOR: {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_CASES,
        Permission.MANAGE_CASES,
        Permission.GENERATE_AI_NARRATIVE,
    },
    Role.SUPERVISOR: {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_CASES,
    },
    Role.READ_ONLY: {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_CASES,
    },
}


def role_has_permission(role: Role, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS[role]
