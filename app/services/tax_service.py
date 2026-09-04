from datetime import date, datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.config import settings
from app.db.models.vehicle import Vehicle
from app.db.models.tax import (
    VehicleTaxRecord,
    VehicleGovernmentCharge,
    VehicleChallan,
    VehicleFASTag,
    TaxType,
    ChargeType,
    TaxStatus,
    ChallanStatus,
    FASTagStatus,
)
from app.db.models.audit_log import AuditLog
from app.schemas.tax import (
    TaxRecordCreate,
    TaxRecordUpdate,
    GovernmentChargeCreate,
    GovernmentChargeUpdate,
    ChallanCreate,
    ChallanUpdate,
    FASTagUpdate,
)
from app.core.exceptions import NotFoundException, BadRequestException, PermissionDeniedException


def compute_tax_status(
    due_date: Optional[date],
    valid_until: Optional[date],
    payment_date: Optional[date],
    warning_days: int = settings.TAX_WARNING_DAYS
) -> TaxStatus:
    today = date.today()
    # 1. Unpaid records
    if not payment_date:
        if due_date and due_date < today:
            return TaxStatus.OVERDUE
        return TaxStatus.PENDING

    # 2. Paid records evaluated by validity
    if valid_until:
        if valid_until < today:
            return TaxStatus.EXPIRED
        elif valid_until <= today + timedelta(days=warning_days):
            return TaxStatus.DUE_SOON

    return TaxStatus.ACTIVE


def sync_record_status(record) -> bool:
    """Recomputes and syncs record status if expired or due soon."""
    new_status = compute_tax_status(record.due_date, record.valid_until, record.payment_date)
    if record.status != new_status:
        record.status = new_status
        return True
    return False


# ==========================================
# Vehicle Taxes
# ==========================================

def get_tax_by_id(db: Session, tax_id: int) -> VehicleTaxRecord:
    tax = db.query(VehicleTaxRecord).filter(VehicleTaxRecord.id == tax_id).first()
    if not tax:
        raise NotFoundException("Tax record not found")
    if sync_record_status(tax):
        db.commit()
        db.refresh(tax)
    return tax


def get_taxes_for_vehicle(db: Session, vehicle_id: int) -> List[VehicleTaxRecord]:
    taxes = db.query(VehicleTaxRecord).filter(
        VehicleTaxRecord.vehicle_id == vehicle_id
    ).order_by(VehicleTaxRecord.valid_until.desc(), VehicleTaxRecord.created_at.desc()).all()
    
    updated = False
    for t in taxes:
        if sync_record_status(t):
            updated = True
    if updated:
        db.commit()
    return taxes


def create_tax_record(db: Session, vehicle_id: int, data: TaxRecordCreate, user_id: int) -> VehicleTaxRecord:
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise NotFoundException("Vehicle not found")

    # Duplicate period check: check for same vehicle, tax_type, and overlapping period
    duplicate = db.query(VehicleTaxRecord).filter(
        VehicleTaxRecord.vehicle_id == vehicle_id,
        VehicleTaxRecord.tax_type == data.tax_type,
        VehicleTaxRecord.period_start == data.period_start,
        VehicleTaxRecord.period_end == data.period_end
    ).first()
    if duplicate:
        raise BadRequestException("A tax record with the exact same tax type and period already exists for this vehicle.")

    status = compute_tax_status(data.due_date, data.valid_until, data.payment_date)

    tax_record = VehicleTaxRecord(
        vehicle_id=vehicle_id,
        tax_type=data.tax_type,
        state=data.state,
        tax_authority=data.tax_authority,
        period_start=data.period_start,
        period_end=data.period_end,
        amount=data.amount,
        payment_date=data.payment_date,
        due_date=data.due_date,
        valid_from=data.valid_from,
        valid_until=data.valid_until,
        status=status,
        payment_reference=data.payment_reference,
        challan_number=data.challan_number,
        notes=data.notes,
        created_by=user_id,
    )
    db.add(tax_record)
    db.commit()
    db.refresh(tax_record)

    audit = AuditLog(
        user_id=user_id,
        action="CREATE_TAX",
        entity_type="tax_record",
        entity_id=tax_record.id,
        details=f"Created {tax_record.tax_type} for vehicle {vehicle.vehicle_number} (Amount: {tax_record.amount})"
    )
    db.add(audit)
    db.commit()

    return tax_record


def update_tax_record(db: Session, tax_id: int, data: TaxRecordUpdate, user_id: int) -> VehicleTaxRecord:
    tax = get_tax_by_id(db, tax_id)
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(tax, field, value)

    tax.status = compute_tax_status(tax.due_date, tax.valid_until, tax.payment_date)
    tax.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(tax)

    audit = AuditLog(
        user_id=user_id,
        action="UPDATE_TAX",
        entity_type="tax_record",
        entity_id=tax.id,
        details=f"Updated tax record {tax.id} for vehicle {tax.vehicle_id}"
    )
    db.add(audit)
    db.commit()
    return tax


def delete_tax_record(db: Session, tax_id: int, user_id: int):
    tax = get_tax_by_id(db, tax_id)
    v_id = tax.vehicle_id
    db.delete(tax)
    db.commit()

    audit = AuditLog(
        user_id=user_id,
        action="DELETE_TAX",
        entity_type="tax_record",
        entity_id=tax_id,
        details=f"Deleted tax record {tax_id} of vehicle {v_id}"
    )
    db.add(audit)
    db.commit()


def attach_tax_receipt(db: Session, tax_id: int, receipt_file_url: str, user_id: int) -> VehicleTaxRecord:
    tax = get_tax_by_id(db, tax_id)
    action = "REPLACE_TAX_RECEIPT" if tax.receipt_file_url else "UPLOAD_TAX_RECEIPT"
    tax.receipt_file_url = receipt_file_url
    tax.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(tax)

    audit = AuditLog(
        user_id=user_id,
        action=action,
        entity_type="tax_record",
        entity_id=tax.id,
        details=f"Uploaded receipt for tax record {tax.id}"
    )
    db.add(audit)
    db.commit()
    return tax


# ==========================================
# Government Charges
# ==========================================

def get_government_charge_by_id(db: Session, charge_id: int) -> VehicleGovernmentCharge:
    charge = db.query(VehicleGovernmentCharge).filter(VehicleGovernmentCharge.id == charge_id).first()
    if not charge:
        raise NotFoundException("Government charge record not found")
    if sync_record_status(charge):
        db.commit()
        db.refresh(charge)
    return charge


def get_government_charges_for_vehicle(db: Session, vehicle_id: int) -> List[VehicleGovernmentCharge]:
    charges = db.query(VehicleGovernmentCharge).filter(
        VehicleGovernmentCharge.vehicle_id == vehicle_id
    ).order_by(VehicleGovernmentCharge.valid_until.desc(), VehicleGovernmentCharge.created_at.desc()).all()

    updated = False
    for c in charges:
        if sync_record_status(c):
            updated = True
    if updated:
        db.commit()
    return charges


def create_government_charge(db: Session, vehicle_id: int, data: GovernmentChargeCreate, user_id: int) -> VehicleGovernmentCharge:
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise NotFoundException("Vehicle not found")

    status = compute_tax_status(data.due_date, data.valid_until, data.payment_date)

    charge = VehicleGovernmentCharge(
        vehicle_id=vehicle_id,
        charge_type=data.charge_type,
        state=data.state,
        authority=data.authority,
        period_start=data.period_start,
        period_end=data.period_end,
        amount=data.amount,
        payment_date=data.payment_date,
        due_date=data.due_date,
        valid_from=data.valid_from,
        valid_until=data.valid_until,
        status=status,
        payment_reference=data.payment_reference,
        notes=data.notes,
        created_by=user_id,
    )
    db.add(charge)
    db.commit()
    db.refresh(charge)

    audit = AuditLog(
        user_id=user_id,
        action="CREATE_GOVERNMENT_CHARGE",
        entity_type="government_charge",
        entity_id=charge.id,
        details=f"Created {charge.charge_type} for vehicle {vehicle.vehicle_number} (Amount: {charge.amount})"
    )
    db.add(audit)
    db.commit()
    return charge


def update_government_charge(db: Session, charge_id: int, data: GovernmentChargeUpdate, user_id: int) -> VehicleGovernmentCharge:
    charge = get_government_charge_by_id(db, charge_id)
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(charge, field, value)

    charge.status = compute_tax_status(charge.due_date, charge.valid_until, charge.payment_date)
    charge.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(charge)

    audit = AuditLog(
        user_id=user_id,
        action="UPDATE_GOVERNMENT_CHARGE",
        entity_type="government_charge",
        entity_id=charge.id,
        details=f"Updated government charge {charge.id}"
    )
    db.add(audit)
    db.commit()
    return charge


def delete_government_charge(db: Session, charge_id: int, user_id: int):
    charge = get_government_charge_by_id(db, charge_id)
    c_id = charge.id
    db.delete(charge)
    db.commit()

    audit = AuditLog(
        user_id=user_id,
        action="DELETE_GOVERNMENT_CHARGE",
        entity_type="government_charge",
        entity_id=c_id,
        details=f"Deleted government charge {c_id}"
    )
    db.add(audit)
    db.commit()


# ==========================================
# Challans
# ==========================================

def get_challan_by_id(db: Session, challan_id: int) -> VehicleChallan:
    challan = db.query(VehicleChallan).filter(VehicleChallan.id == challan_id).first()
    if not challan:
        raise NotFoundException("Challan record not found")
    return challan


def get_challans_for_vehicle(db: Session, vehicle_id: int) -> List[VehicleChallan]:
    return db.query(VehicleChallan).filter(
        VehicleChallan.vehicle_id == vehicle_id
    ).order_by(VehicleChallan.issue_date.desc()).all()


def create_challan(db: Session, vehicle_id: int, data: ChallanCreate, user_id: int) -> VehicleChallan:
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise NotFoundException("Vehicle not found")

    challan = VehicleChallan(
        vehicle_id=vehicle_id,
        challan_number=data.challan_number,
        authority=data.authority,
        reason=data.reason,
        issue_date=data.issue_date,
        amount=data.amount,
        due_date=data.due_date,
        payment_date=data.payment_date,
        status=data.status,
        notes=data.notes,
        created_by=user_id,
    )
    db.add(challan)
    db.commit()
    db.refresh(challan)

    audit = AuditLog(
        user_id=user_id,
        action="CREATE_CHALLAN",
        entity_type="challan",
        entity_id=challan.id,
        details=f"Recorded challan {challan.challan_number} for {vehicle.vehicle_number}"
    )
    db.add(audit)
    db.commit()
    return challan


def update_challan(db: Session, challan_id: int, data: ChallanUpdate, user_id: int) -> VehicleChallan:
    challan = get_challan_by_id(db, challan_id)
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(challan, field, value)

    challan.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(challan)

    audit = AuditLog(
        user_id=user_id,
        action="UPDATE_CHALLAN",
        entity_type="challan",
        entity_id=challan.id,
        details=f"Updated challan {challan.challan_number}"
    )
    db.add(audit)
    db.commit()
    return challan


def delete_challan(db: Session, challan_id: int, user_id: int):
    challan = get_challan_by_id(db, challan_id)
    c_id = challan.id
    db.delete(challan)
    db.commit()

    audit = AuditLog(
        user_id=user_id,
        action="DELETE_CHALLAN",
        entity_type="challan",
        entity_id=c_id,
        details=f"Deleted challan {c_id}"
    )
    db.add(audit)
    db.commit()


# ==========================================
# FASTag
# ==========================================

def get_or_create_fastag(db: Session, vehicle_id: int) -> VehicleFASTag:
    fastag = db.query(VehicleFASTag).filter(VehicleFASTag.vehicle_id == vehicle_id).first()
    if not fastag:
        fastag = VehicleFASTag(
            vehicle_id=vehicle_id,
            tag_status=FASTagStatus.ACTIVE
        )
        db.add(fastag)
        db.commit()
        db.refresh(fastag)
    return fastag


def update_fastag(db: Session, vehicle_id: int, data: FASTagUpdate) -> VehicleFASTag:
    fastag = get_or_create_fastag(db, vehicle_id)
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(fastag, k, v)
    fastag.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(fastag)
    return fastag


# ==========================================
# Fleet Admin Queries & Compliance Summary
# ==========================================

def get_fleet_taxes(
    db: Session,
    vehicle_id: Optional[int] = None,
    tax_type: Optional[str] = None,
    state: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    skip: int = 0,
    limit: int = 100
) -> List[VehicleTaxRecord]:
    query = db.query(VehicleTaxRecord)

    if vehicle_id:
        query = query.filter(VehicleTaxRecord.vehicle_id == vehicle_id)
    if tax_type:
        query = query.filter(VehicleTaxRecord.tax_type == tax_type)
    if state:
        query = query.filter(VehicleTaxRecord.state == state)
    if status:
        query = query.filter(VehicleTaxRecord.status == status)
    if date_from:
        query = query.filter(VehicleTaxRecord.valid_until >= date_from)
    if date_to:
        query = query.filter(VehicleTaxRecord.valid_until <= date_to)

    taxes = query.order_by(VehicleTaxRecord.valid_until.asc()).offset(skip).limit(limit).all()
    for t in taxes:
        sync_record_status(t)
    db.commit()
    return taxes


def get_taxes_by_status(db: Session, status: TaxStatus) -> List[VehicleTaxRecord]:
    # Sync all taxes first so status is fresh
    all_taxes = db.query(VehicleTaxRecord).all()
    for t in all_taxes:
        sync_record_status(t)
    db.commit()

    return db.query(VehicleTaxRecord).filter(VehicleTaxRecord.status == status).all()


def get_tax_compliance_summary(db: Session) -> dict:
    all_taxes = db.query(VehicleTaxRecord).all()
    for t in all_taxes:
        sync_record_status(t)
    db.commit()

    active = db.query(VehicleTaxRecord).filter(VehicleTaxRecord.status == TaxStatus.ACTIVE).count()
    due_soon = db.query(VehicleTaxRecord).filter(VehicleTaxRecord.status == TaxStatus.DUE_SOON).count()
    overdue = db.query(VehicleTaxRecord).filter(VehicleTaxRecord.status == TaxStatus.OVERDUE).count()
    expired = db.query(VehicleTaxRecord).filter(VehicleTaxRecord.status == TaxStatus.EXPIRED).count()
    unpaid_challans = db.query(VehicleChallan).filter(VehicleChallan.status == ChallanStatus.UNPAID).count()

    return {
        "active_taxes": active,
        "due_soon_taxes": due_soon,
        "overdue_taxes": overdue,
        "expired_taxes": expired,
        "unpaid_challans": unpaid_challans
    }
