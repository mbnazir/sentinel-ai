from app.security.domain.roles import Role
from app.sso.services.sso_role_mapper import SSORoleMapper


def test_maps_admin_group_to_admin_role() -> None:
    assert SSORoleMapper().map_groups_to_roles(["Sentinel-Admin"]) == [Role.ADMIN]


def test_defaults_to_read_only() -> None:
    assert SSORoleMapper().map_groups_to_roles(["Unknown"]) == [Role.READ_ONLY]
