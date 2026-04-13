from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import RoleEnum


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: RoleEnum
    mfa_enabled: bool
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
