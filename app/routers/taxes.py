import os
from typing import List, Optional
from fastapi import APIRouter, Depends, status, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.user import User, UserRole
from app.core.dependencies import get_current_user, get_current_admin
from app.core.exceptions import PermissionDeniedException, NotFoundException, CredentialsException
from app.core.config import settings
from app.core.security import decode_token
from app.utils.file_validation import validate_and_save_upload_file
from app.services import vehicle_service, tax_service
from app.schemas.tax import (
    TaxRecordCreate,
    TaxRecordUpdate,
    TaxRecordResponse,
    GovernmentChargeCreate,
    GovernmentChargeUpdate,
    GovernmentChargeResponse,
    ChallanCreate,
    ChallanUpdate,
    ChallanResponse,
    FASTagUpdate,
    FASTagResponse,
)

router = APIRouter(tags=["Vehicle Taxes & Government Charges"])


def verify_vehicle_access(db: Session, vehicle_id: int, current_user: User):
    """Verifies that the vehicle exists and that the user is authorized (Admin or assigned Driver)."""
    vehicle = vehicle_service.get_vehicle_by_id(db, vehicle_id)
    if current_user.role == UserRole.DRIVER:
        assigned_vehicles = vehicle_service.get_driver_assigned_vehicles(db, current_user.id)
        if vehicle.id not in [v.id for v in assigned_vehicles]:
            raise PermissionDeniedException("Access denied: You are not assigned to this vehicle")
    return vehicle


# ==========================================
# 1. Vehicle Taxes Endpoints
# ==========================================

@router.post("/vehicles/{vehicle_id}/taxes", response_model=TaxRecordResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle_tax(
    vehicle_id: int,
    data: TaxRecordCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    verify_vehicle_access(db, vehicle_id, admin)
    return tax_service.create_tax_record(db, vehicle_id, data, admin.id)


@router.get("/vehicles/{vehicle_id}/taxes", response_model=List[TaxRecordResponse])
def get_vehicle_taxes(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verify_vehicle_access(db, vehicle_id, current_user)
    return tax_service.get_taxes_for_vehicle(db, vehicle_id)


@router.get("/vehicles/{vehicle_id}/taxes/{tax_id}", response_model=TaxRecordResponse)
def get_vehicle_tax(
    vehicle_id: int,
    tax_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verify_vehicle_access(db, vehicle_id, current_user)
    tax = tax_service.get_tax_by_id(db, tax_id)
    if tax.vehicle_id != vehicle_id:
        raise NotFoundException("Tax record not found for this vehicle")
    return tax


@router.patch("/vehicles/{vehicle_id}/taxes/{tax_id}", response_model=TaxRecordResponse)
def update_vehicle_tax(
    vehicle_id: int,
    tax_id: int,
    data: TaxRecordUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    verify_vehicle_access(db, vehicle_id, admin)
    tax = tax_service.get_tax_by_id(db, tax_id)
    if tax.vehicle_id != vehicle_id:
        raise NotFoundException("Tax record not found for this vehicle")
    return tax_service.update_tax_record(db, tax_id, data, admin.id)


@router.delete("/vehicles/{vehicle_id}/taxes/{tax_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle_tax(
    vehicle_id: int,
    tax_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    verify_vehicle_access(db, vehicle_id, admin)
    tax = tax_service.get_tax_by_id(db, tax_id)
    if tax.vehicle_id != vehicle_id:
        raise NotFoundException("Tax record not found for this vehicle")
    tax_service.delete_tax_record(db, tax_id, admin.id)


@router.post("/vehicles/{vehicle_id}/taxes/{tax_id}/receipt", response_model=TaxRecordResponse)
def upload_tax_receipt(
    vehicle_id: int,
    tax_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verify_vehicle_access(db, vehicle_id, current_user)
    tax = tax_service.get_tax_by_id(db, tax_id)
    if tax.vehicle_id != vehicle_id:
        raise NotFoundException("Tax record not found for this vehicle")

    filename, file_url, mime_type, file_size = validate_and_save_upload_file(file, vehicle_id)
    return tax_service.attach_tax_receipt(db, tax_id, file_url, current_user.id)


# ==========================================
# 2. Government Charges Endpoints
# ==========================================

@router.post("/vehicles/{vehicle_id}/government-charges", response_model=GovernmentChargeResponse, status_code=status.HTTP_201_CREATED)
def create_government_charge(
    vehicle_id: int,
    data: GovernmentChargeCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    verify_vehicle_access(db, vehicle_id, admin)
    return tax_service.create_government_charge(db, vehicle_id, data, admin.id)


@router.get("/vehicles/{vehicle_id}/government-charges", response_model=List[GovernmentChargeResponse])
def get_government_charges(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verify_vehicle_access(db, vehicle_id, current_user)
    return tax_service.get_government_charges_for_vehicle(db, vehicle_id)


@router.get("/vehicles/{vehicle_id}/government-charges/{charge_id}", response_model=GovernmentChargeResponse)
def get_government_charge(
    vehicle_id: int,
    charge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verify_vehicle_access(db, vehicle_id, current_user)
    charge = tax_service.get_government_charge_by_id(db, charge_id)
    if charge.vehicle_id != vehicle_id:
        raise NotFoundException("Government charge not found for this vehicle")
    return charge


@router.patch("/vehicles/{vehicle_id}/government-charges/{charge_id}", response_model=GovernmentChargeResponse)
def update_government_charge(
    vehicle_id: int,
    charge_id: int,
    data: GovernmentChargeUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    verify_vehicle_access(db, vehicle_id, admin)
    charge = tax_service.get_government_charge_by_id(db, charge_id)
    if charge.vehicle_id != vehicle_id:
        raise NotFoundException("Government charge not found for this vehicle")
    return tax_service.update_government_charge(db, charge_id, data, admin.id)


@router.delete("/vehicles/{vehicle_id}/government-charges/{charge_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_government_charge(
    vehicle_id: int,
    charge_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    verify_vehicle_access(db, vehicle_id, admin)
    charge = tax_service.get_government_charge_by_id(db, charge_id)
    if charge.vehicle_id != vehicle_id:
        raise NotFoundException("Government charge not found for this vehicle")
    tax_service.delete_government_charge(db, charge_id, admin.id)


# ==========================================
# 3. Challans Endpoints
# ==========================================

@router.post("/vehicles/{vehicle_id}/challans", response_model=ChallanResponse, status_code=status.HTTP_201_CREATED)
def create_challan(
    vehicle_id: int,
    data: ChallanCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    verify_vehicle_access(db, vehicle_id, admin)
    return tax_service.create_challan(db, vehicle_id, data, admin.id)


@router.get("/vehicles/{vehicle_id}/challans", response_model=List[ChallanResponse])
def get_challans(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verify_vehicle_access(db, vehicle_id, current_user)
    return tax_service.get_challans_for_vehicle(db, vehicle_id)


@router.get("/vehicles/{vehicle_id}/challans/{challan_id}", response_model=ChallanResponse)
def get_challan(
    vehicle_id: int,
    challan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verify_vehicle_access(db, vehicle_id, current_user)
    challan = tax_service.get_challan_by_id(db, challan_id)
    if challan.vehicle_id != vehicle_id:
        raise NotFoundException("Challan record not found for this vehicle")
    return challan


@router.patch("/vehicles/{vehicle_id}/challans/{challan_id}", response_model=ChallanResponse)
def update_challan(
    vehicle_id: int,
    challan_id: int,
    data: ChallanUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    verify_vehicle_access(db, vehicle_id, admin)
    challan = tax_service.get_challan_by_id(db, challan_id)
    if challan.vehicle_id != vehicle_id:
        raise NotFoundException("Challan record not found for this vehicle")
    return tax_service.update_challan(db, challan_id, data, admin.id)


@router.delete("/vehicles/{vehicle_id}/challans/{challan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_challan(
    vehicle_id: int,
    challan_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    verify_vehicle_access(db, vehicle_id, admin)
    challan = tax_service.get_challan_by_id(db, challan_id)
    if challan.vehicle_id != vehicle_id:
        raise NotFoundException("Challan record not found for this vehicle")
    tax_service.delete_challan(db, challan_id, admin.id)


# ==========================================
# 4. FASTag Endpoints
# ==========================================

@router.get("/vehicles/{vehicle_id}/fastag", response_model=FASTagResponse)
def get_fastag_info(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verify_vehicle_access(db, vehicle_id, current_user)
    return tax_service.get_or_create_fastag(db, vehicle_id)


@router.put("/vehicles/{vehicle_id}/fastag", response_model=FASTagResponse)
def update_fastag_info(
    vehicle_id: int,
    data: FASTagUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    verify_vehicle_access(db, vehicle_id, admin)
    return tax_service.update_fastag(db, vehicle_id, data)


# ==========================================
# 5. Authenticated Receipt Download
# ==========================================

@router.get("/taxes/receipt/{filename}")
def serve_tax_receipt(
    filename: str,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    if not token:
        raise CredentialsException("Authentication token required to view receipt")
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.is_active:
            raise CredentialsException("User account invalid or inactive")
    except Exception:
        raise CredentialsException("Invalid or expired token")

    safe_filename = os.path.basename(filename)
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
    if not os.path.exists(file_path):
        raise NotFoundException("Requested receipt file not found")

    return FileResponse(
        file_path,
        headers={"Content-Disposition": f"inline; filename=\"{safe_filename}\""}
    )
