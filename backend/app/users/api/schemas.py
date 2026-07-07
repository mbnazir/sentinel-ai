from pydantic import BaseModel


class CreateUserRequest(BaseModel):
    organization_id: str
    email: str
    full_name: str
    password: str
    roles: list[str]


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    user_id: str
    organization_id: str
    email: str
    full_name: str
    roles: list[str]
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
