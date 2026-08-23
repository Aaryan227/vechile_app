from typing import Generator, Optional
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_token
from app.core.exceptions import CredentialsException, PermissionDeniedException
from app.db.session import get_db
from app.db.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    try:
        payload = decode_token(token)
        user_id: Optional[str] = payload.get("sub")
        token_type: Optional[str] = payload.get("type")
        if user_id is None or token_type != "access":
            raise CredentialsException("Invalid token payload")
    except JWTError:
        raise CredentialsException("Could not validate authentication credentials")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise CredentialsException("User associated with token not found")
    if not user.is_active:
        raise PermissionDeniedException("User account is inactive")
    
    return user

def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise PermissionDeniedException("Admin role required for this action")
    return current_user

def get_current_driver(
    current_user: User = Depends(get_current_user)
) -> User:
    # Allows drivers (and admins testing driver endpoints)
    if current_user.role not in [UserRole.DRIVER, UserRole.ADMIN]:
        raise PermissionDeniedException("Driver role required for this action")
    return current_user
