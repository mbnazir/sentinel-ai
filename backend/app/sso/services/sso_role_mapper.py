from app.security.domain.roles import Role


class SSORoleMapper:
    def map_groups_to_roles(self, groups: list[str]) -> list[Role]:
        normalized = {group.lower() for group in groups}

        if any("admin" in group for group in normalized):
            return [Role.ADMIN]
        if any("compliance" in group for group in normalized):
            return [Role.COMPLIANCE]
        if any("investigator" in group for group in normalized):
            return [Role.INVESTIGATOR]
        if any("supervisor" in group for group in normalized):
            return [Role.SUPERVISOR]

        return [Role.READ_ONLY]
