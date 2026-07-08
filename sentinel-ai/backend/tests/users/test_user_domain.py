from datetime import datetime, timezone

from app.security.domain.roles import Role
from app.users.domain.user import User


def test_user_domain_model() -> None:
    user = User(
        user_id="U1",
        organization_id="ORG1",
        email="user@example.com",
        full_name="User Example",
        roles=[Role.INVESTIGATOR],
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )

    assert user.email == "user@example.com"
    assert user.roles == [Role.INVESTIGATOR]
