from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.core.dependencies import get_current_master, get_current_master_or_admin
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse
from app.services import vehicle_service

router = APIRouter(prefix="/vehicles", tags=["Vehicles Management"])

def populate_vehicle_response(vehicle) -> VehicleResponse:
    return VehicleResponse.model_validate(vehicle)

@router.get("", response_model=List[VehicleResponse])
def list_vehicles(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_master_or_admin)
):
    """List all vehicles (accessible to Master operations and Admin monitors)."""
    vehicles = vehicle_service.get_vehicles(db, skip=skip, limit=limit, status=status)
    return [populate_vehicle_response(v) for v in vehicles]

@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    data: VehicleCreate,
    db: Session = Depends(get_db),
    master: User = Depends(get_current_master)
):
    """Master endpoint to register a new vehicle."""
    vehicle = vehicle_service.create_vehicle(db, data, master.id)
    return populate_vehicle_response(vehicle)

@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_master_or_admin)
):
    """Get vehicle details (accessible to Master operations and Admin monitors)."""
    vehicle = vehicle_service.get_vehicle_by_id(db, vehicle_id)
    return populate_vehicle_response(vehicle)

@router.patch("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_id: int,
    data: VehicleUpdate,
    db: Session = Depends(get_db),
    master: User = Depends(get_current_master)
):
    """Master endpoint to update vehicle details."""
    vehicle = vehicle_service.update_vehicle(db, vehicle_id, data, master.id)
    return populate_vehicle_response(vehicle)

@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    master: User = Depends(get_current_master)
):
    """Master endpoint to delete a vehicle."""
    vehicle_service.delete_vehicle(db, vehicle_id, master.id)
