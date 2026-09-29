from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User, UserRole
from app.db.models.vehicle import Vehicle
from app.core.dependencies import get_current_user, get_current_master
from app.schemas.firm import FirmCreate, FirmUpdate, FirmResponse
from app.services import firm_service

router = APIRouter(prefix="/firms", tags=["Firms Management"])

def _populate_firm_response(db: Session, firm) -> FirmResponse:
    res = FirmResponse.model_validate(firm)
    res.vehicle_count = db.query(Vehicle).filter(Vehicle.firm_id == firm.id).count()
    return res

@router.get("", response_model=List[FirmResponse])
def list_firms(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    firms = firm_service.get_firms(db, skip=skip, limit=limit, is_active=is_active)
    return [_populate_firm_response(db, f) for f in firms]

@router.post("", response_model=FirmResponse, status_code=status.HTTP_201_CREATED)
def create_firm(
    data: FirmCreate,
    db: Session = Depends(get_db),
    master: User = Depends(get_current_master)
):
    firm = firm_service.create_firm(db, data, master.id)
    return _populate_firm_response(db, firm)

@router.get("/{firm_id}", response_model=FirmResponse)
def get_firm(
    firm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    firm = firm_service.get_firm_by_id(db, firm_id)
    return _populate_firm_response(db, firm)

@router.patch("/{firm_id}", response_model=FirmResponse)
def update_firm(
    firm_id: int,
    data: FirmUpdate,
    db: Session = Depends(get_db),
    master: User = Depends(get_current_master)
):
    firm = firm_service.update_firm(db, firm_id, data, master.id)
    return _populate_firm_response(db, firm)

@router.delete("/{firm_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_firm(
    firm_id: int,
    db: Session = Depends(get_db),
    master: User = Depends(get_current_master)
):
    firm_service.delete_firm(db, firm_id, master.id)
