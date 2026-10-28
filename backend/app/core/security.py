from datetime import UTC, datetime, timedelta
import jwt
from app.core.config import settings

ISSUER="sentinel-ai"

def create_access_token(subject:str,role:str)->str:
    now=datetime.now(UTC)
    payload={"sub":subject,"role":role,"iat":now,"nbf":now,"exp":now+timedelta(minutes=settings.jwt_access_minutes),"iss":ISSUER,"aud":settings.jwt_audience}
    return jwt.encode(payload,settings.jwt_secret,algorithm=settings.jwt_algorithm)

def decode_access_token(token:str)->dict[str,object]:
    return jwt.decode(token,settings.jwt_secret,algorithms=[settings.jwt_algorithm],issuer=ISSUER,audience=settings.jwt_audience,options={"require":["sub","role","iat","exp","iss","aud"]})
