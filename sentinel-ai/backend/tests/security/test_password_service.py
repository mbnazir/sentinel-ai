from app.security.services.password_service import PasswordService


def test_password_hash_and_verify() -> None:
    service = PasswordService()
    hashed = service.hash_password("strong-password")
    assert hashed != "strong-password"
    assert service.verify_password("strong-password", hashed) is True
    assert service.verify_password("wrong", hashed) is False
