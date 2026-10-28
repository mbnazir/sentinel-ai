from enum import StrEnum
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.security import decode_access_token

bearer = HTTPBearer(auto_error=False)

class Role(StrEnum):
    VIEWER="viewer"
    INVESTIGATOR="investigator"
    MANAGER="manager"
    ADMIN="admin"

class Principal(BaseModel):
    subject:str
    role:Role

async def current_principal(credentials:Annotated[HTTPAuthorizationCredentials|None,Depends(bearer)]) -> Principal:
    if credentials is None:
        raise HTTPException(status_code=401,detail="authentication required")
    try:
        claims=decode_access_token(credentials.credentials)
        return Principal(subject=str(claims["sub"]),role=Role(str(claims["role"])))
    except Exception as exc:
        raise HTTPException(status_code=401,detail="invalid or expired token") from exc

def require_roles(*roles:Role):
    async def dependency(principal:Annotated[Principal,Depends(current_principal)]) -> Principal:
        if principal.role not in roles:
            raise HTTPException(status_code=403,detail="insufficient permissions")
        return principal
    return dependency
