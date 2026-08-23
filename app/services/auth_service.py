from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.models.user import User, UserRole
from app.db.models.audit_log import AuditLog
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import BadRequestException, ConflictException, CredentialsException
from app.schemas.auth import RegisterRequest, AdminUserCreate

def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise CredentialsException("Invalid email or password")
    if not user.is_active:
        raise BadRequestException("User account is inactive")
    
    user.last_login_at = datetime.now(timezone.utc)
    audit = AuditLog(user_id=user.id, action="LOGIN", entity_type="user", entity_id=user.id)
    db.add(audit)
    db.commit()
    db.refresh(user)
    return user

def register_user(db: Session, data: RegisterRequest) -> User:
    if db.query(User).filter(User.email == data.email).first():
        raise ConflictException("Email is already registered")
    if data.phone and db.query(User).filter(User.phone == data.phone).first():
        raise ConflictException("Phone number is already registered")
    
    if data.role == UserRole.ADMIN:
        if not data.admin_access_code or data.admin_access_code != settings.ADMIN_ACCESS_CODE:
            raise BadRequestException("Invalid Admin Access Code")
    
    user = User(
        name=data.name,
        email=data.email,
        phone=data.phone,
        password_hash=get_password_hash(data.password),
        role=data.role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    audit = AuditLog(user_id=user.id, action="REGISTER", entity_type="user", entity_id=user.id)
    db.add(audit)
    db.commit()
    return user

def register_driver(db: Session, data: RegisterRequest) -> User:
    return register_user(db, data)

def create_user_by_admin(db: Session, data: AdminUserCreate, admin_id: int) -> User:
    if db.query(User).filter(User.email == data.email).first():
        raise ConflictException("Email is already registered")
    if data.phone and db.query(User).filter(User.phone == data.phone).first():
        raise ConflictException("Phone number is already registered")
    
    user = User(
        name=data.name,
        email=data.email,
        phone=data.phone,
        password_hash=get_password_hash(data.password),
        role=data.role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    audit = AuditLog(user_id=admin_id, action="CREATE_USER", entity_type="user", entity_id=user.id)
    db.add(audit)
    db.commit()
    return user

def change_user_password(db: Session, user: User, old_password: str, new_password: str) -> None:
    if not verify_password(old_password, user.password_hash):
        raise BadRequestException("Incorrect old password")
    
    user.password_hash = get_password_hash(new_password)
    db.commit()
    
    audit = AuditLog(user_id=user.id, action="CHANGE_PASSWORD", entity_type="user", entity_id=user.id)
    db.add(audit)
    db.commit()
