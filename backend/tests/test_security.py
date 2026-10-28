from app.core.security import create_access_token, decode_access_token


def test_jwt_round_trip() -> None:
    token = create_access_token("user-1", "investigator")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-1"
    assert payload["role"] == "investigator"
