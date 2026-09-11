from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
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
    role: UserRole = UserRole.MASTER
    access_code: Optional[str] = None
    admin_access_code: Optional[str] = None

    @field_validator("phone", mode="before")
    @classmethod
    def clean_phone(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v_clean = v.strip()
            return v_clean if v_clean else None
        return v

    @field_validator("access_code", "admin_access_code", mode="before")
    @classmethod
    def clean_code(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v_clean = v.strip()
            # If Swagger placeholder "string" was sent, treat as None
            if not v_clean or v_clean.lower() == "string":
                return None
            return v_clean
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Fleet Master",
                "email": "master.new@vahaansetu.com",
                "phone": "9811223344",
                "password": "MasterPassword123",
                "role": "master",
                "access_code": "MASTER_ACCESS_2026"
            }
        }
    }

class AdminUserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.MASTER

    @field_validator("phone", mode="before")
    @classmethod
    def clean_phone(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v_clean = v.strip()
            return v_clean if v_clean else None
        return v

class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)

