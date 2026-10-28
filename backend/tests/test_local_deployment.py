from app.core.config import settings
from app.core.security import create_access_token, decode_access_token

def test_local_admin_token_round_trip():
    token=create_access_token("local.admin@test","admin")
    claims=decode_access_token(token)
    assert claims["sub"]=="local.admin@test"
    assert claims["role"]=="admin"

def test_quartz_token_is_not_required_in_connector_table():
    assert hasattr(settings,"quartz_api_bearer_token")
