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

from sqlalchemy.exc import IntegrityError

def register_user(db: Session, data: RegisterRequest) -> User:
    # Normalize phone: empty strings/whitespace become None so DB uniqueness constraint isn't violated
    phone = data.phone.strip() if (data.phone and isinstance(data.phone, str) and data.phone.strip()) else None

    if db.query(User).filter(User.email == data.email.strip().lower()).first():
        raise ConflictException("Email is already registered")
    if phone and db.query(User).filter(User.phone == phone).first():
        raise ConflictException("Phone number is already registered")
    
    # Extract entered codes, stripping whitespace and ignoring placeholder strings
    raw_codes = [c.strip() for c in [data.access_code, data.admin_access_code] if c and isinstance(c, str) and c.strip()]
    entered_codes = [c for c in raw_codes if c.lower() != "string"]

    if data.role == UserRole.MASTER:
        has_valid_code = any(c.upper() == settings.MASTER_ACCESS_CODE.upper() for c in entered_codes)
        if not has_valid_code:
            raise BadRequestException("Invalid Master Access Code")
    elif data.role == UserRole.ADMIN:
        has_valid_code = any(c.upper() == settings.ADMIN_ACCESS_CODE.upper() for c in entered_codes)
        if not has_valid_code:
            raise BadRequestException("Invalid Admin Access Code")
    elif data.role == UserRole.DRIVER:
        raise BadRequestException("Driver registration is no longer supported")
    
    user = User(
        name=data.name.strip(),
        email=data.email.strip().lower(),
        phone=phone,
        password_hash=get_password_hash(data.password),
        role=data.role,
        is_active=True
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        
        audit = AuditLog(user_id=user.id, action="REGISTER", entity_type="user", entity_id=user.id)
        db.add(audit)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        err_msg = str(e).lower()
        if "users.email" in err_msg or "unique constraint failed: users.email" in err_msg:
            raise ConflictException("Email is already registered")
        elif "users.phone" in err_msg or "unique constraint failed: users.phone" in err_msg:
            raise ConflictException("Phone number is already registered")
        else:
            raise ConflictException("A user with this email or phone number already exists")
            
    return user

def register_driver(db: Session, data: RegisterRequest) -> User:
    return register_user(db, data)

def create_user_by_admin(db: Session, data: AdminUserCreate, admin_id: int) -> User:
    phone = data.phone.strip() if (data.phone and isinstance(data.phone, str) and data.phone.strip()) else None

    if db.query(User).filter(User.email == data.email.strip().lower()).first():
        raise ConflictException("Email is already registered")
    if phone and db.query(User).filter(User.phone == phone).first():
        raise ConflictException("Phone number is already registered")
    
    user = User(
        name=data.name.strip(),
        email=data.email.strip().lower(),
        phone=phone,
        password_hash=get_password_hash(data.password),
        role=data.role,
        is_active=True
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        
        audit = AuditLog(user_id=admin_id, action="CREATE_USER", entity_type="user", entity_id=user.id)
        db.add(audit)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        err_msg = str(e).lower()
        if "users.email" in err_msg or "unique constraint failed: users.email" in err_msg:
            raise ConflictException("Email is already registered")
        elif "users.phone" in err_msg or "unique constraint failed: users.phone" in err_msg:
            raise ConflictException("Phone number is already registered")
        else:
            raise ConflictException("A user with this email or phone number already exists")
            
    return user

def change_user_password(db: Session, user: User, old_password: str, new_password: str) -> None:
    if not verify_password(old_password, user.password_hash):
        raise BadRequestException("Incorrect old password")
    
    user.password_hash = get_password_hash(new_password)
    db.commit()
    
    audit = AuditLog(user_id=user.id, action="CHANGE_PASSWORD", entity_type="user", entity_id=user.id)
    db.add(audit)
    db.commit()
