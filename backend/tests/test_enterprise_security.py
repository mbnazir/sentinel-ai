from app.core.auth import Role
from app.core.security import create_access_token, decode_access_token

def test_token_has_required_enterprise_claims():
    token=create_access_token("investigator@example.test",Role.INVESTIGATOR.value)
    claims=decode_access_token(token)
    assert claims["sub"]=="investigator@example.test"
    assert claims["role"]=="investigator"
    assert claims["iss"]=="sentinel-ai"
    assert claims["aud"]=="sentinel-ai-api"

def test_roles_are_explicit():
    assert {x.value for x in Role}=={"viewer","investigator","manager","admin"}
