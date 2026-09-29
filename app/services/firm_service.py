from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models.firm import Firm
from app.db.models.vehicle import Vehicle
from app.db.models.audit_log import AuditLog
from app.schemas.firm import FirmCreate, FirmUpdate
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException

def create_firm(db: Session, data: FirmCreate, user_id: int) -> Firm:
    existing = db.query(Firm).filter(Firm.name.ilike(data.name.strip())).first()
    if existing:
        raise ConflictException(f"A firm with name '{data.name.strip()}' already exists")
    
    firm = Firm(
        name=data.name.strip(),
        registration_number=data.registration_number.strip() if data.registration_number else None,
        contact_person=data.contact_person.strip() if data.contact_person else None,
        phone=data.phone.strip() if data.phone else None,
        is_active=data.is_active,
        created_by=user_id
    )
    db.add(firm)
    db.commit()
    db.refresh(firm)

    audit = AuditLog(user_id=user_id, action="CREATE_FIRM", entity_type="firm", entity_id=firm.id)
    db.add(audit)
    db.commit()
    return firm

def get_firms(db: Session, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None) -> List[Firm]:
    query = db.query(Firm)
    if is_active is not None:
        query = query.filter(Firm.is_active == is_active)
    return query.order_by(Firm.name.asc()).offset(skip).limit(limit).all()

def get_firm_by_id(db: Session, firm_id: int) -> Firm:
    firm = db.query(Firm).filter(Firm.id == firm_id).first()
    if not firm:
        raise NotFoundException("Firm not found")
    return firm

def update_firm(db: Session, firm_id: int, data: FirmUpdate, user_id: int) -> Firm:
    firm = get_firm_by_id(db, firm_id)
    update_data = data.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"]:
        name_clean = update_data["name"].strip()
        existing = db.query(Firm).filter(Firm.name.ilike(name_clean), Firm.id != firm_id).first()
        if existing:
            raise ConflictException(f"Another firm with name '{name_clean}' already exists")
        firm.name = name_clean

    for field in ["registration_number", "contact_person", "phone", "is_active"]:
        if field in update_data:
            setattr(firm, field, update_data[field])

    firm.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(firm)

    audit = AuditLog(user_id=user_id, action="UPDATE_FIRM", entity_type="firm", entity_id=firm.id)
    db.add(audit)
    db.commit()
    return firm

def delete_firm(db: Session, firm_id: int, user_id: int) -> None:
    firm = get_firm_by_id(db, firm_id)
    # Check if vehicles are linked to this firm
    vehicles_count = db.query(Vehicle).filter(Vehicle.firm_id == firm_id).count()
    if vehicles_count > 0:
        raise BadRequestException(f"Cannot delete firm '{firm.name}' because {vehicles_count} vehicle(s) are assigned to it. Reassign vehicles first.")

    db.delete(firm)
    db.commit()

    audit = AuditLog(user_id=user_id, action="DELETE_FIRM", entity_type="firm", entity_id=firm_id)
    db.add(audit)
    db.commit()
