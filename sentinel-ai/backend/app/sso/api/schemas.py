from pydantic import BaseModel


class SSOCallbackRequest(BaseModel):
    code: str
    redirect_uri: str


class SSOLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    provider: str
