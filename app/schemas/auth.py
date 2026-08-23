from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.db.models.user import UserRole

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[int] = None
    role: Optional[UserRole] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.DRIVER
    admin_access_code: Optional[str] = None

class AdminUserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.DRIVER

class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)
