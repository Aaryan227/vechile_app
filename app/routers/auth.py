from typing import Optional
from fastapi import APIRouter, Depends, status, Request, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User, UserRole
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.exceptions import CredentialsException, BadRequestException
from app.schemas.auth import LoginRequest, RegisterRequest, Token, PasswordChange
from app.schemas.user import UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Public registration for DRIVER or ADMIN accounts (requires admin_access_code for ADMIN)."""
    return auth_service.register_user(db, data)

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    db: Session = Depends(get_db),
    login_data: Optional[LoginRequest] = Body(None)
):
    """Authenticate user and return JWT access and refresh tokens (supports OAuth2 modal & JSON)."""
    email = None
    password = None

    if login_data and login_data.email and login_data.password:
        email = login_data.email
        password = login_data.password
    else:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                body = await request.json()
                email = body.get("email") or body.get("username")
                password = body.get("password")
            except Exception:
                pass
        else:
            try:
                form = await request.form()
                email = form.get("username") or form.get("email")
                password = form.get("password")
            except Exception:
                pass

    if not email or not password:
        raise BadRequestException("Email/username and password are required")

    user = auth_service.authenticate_user(db, email, password)
    access_token = create_access_token(subject=user.id, role=user.role.value)
    refresh_token = create_refresh_token(subject=user.id, role=user.role.value)
    return Token(access_token=access_token, refresh_token=refresh_token)

@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Generate a new access token using a valid refresh token."""
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise CredentialsException("Invalid token type")
        user_id = payload.get("sub")
    except Exception:
        raise CredentialsException("Invalid refresh token")
        
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise CredentialsException("User account invalid or inactive")
        
    new_access_token = create_access_token(subject=user.id, role=user.role.value)
    new_refresh_token = create_refresh_token(subject=user.id, role=user.role.value)
    return Token(access_token=new_access_token, refresh_token=new_refresh_token)

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get profile of current authenticated user."""
    return current_user

@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(data: PasswordChange, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Change password for current authenticated user."""
    auth_service.change_user_password(db, current_user, data.old_password, data.new_password)
    return {"message": "Password changed successfully"}

@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(current_user: User = Depends(get_current_user)):
    """Client side logout confirmation."""
    return {"message": "Logout successful"}
