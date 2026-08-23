from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User, UserRole
from app.core.dependencies import get_current_user, get_current_admin
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse, VehicleAssignRequest
from app.schemas.user import UserResponse
from app.services import vehicle_service
from app.core.exceptions import PermissionDeniedException

router = APIRouter(prefix="/vehicles", tags=["Vehicles Management"])

def populate_vehicle_response(db: Session, vehicle) -> VehicleResponse:
    res = VehicleResponse.model_validate(vehicle)
    active_driver = vehicle_service.get_active_driver_for_vehicle(db, vehicle.id)
    if active_driver:
        res.active_driver = UserResponse.model_validate(active_driver)
    return res

@router.get("", response_model=List[VehicleResponse])
def list_vehicles(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.ADMIN:
        vehicles = vehicle_service.get_vehicles(db, skip=skip, limit=limit, status=status)
    else:
        vehicles = vehicle_service.get_driver_assigned_vehicles(db, current_user.id)
        
    return [populate_vehicle_response(db, v) for v in vehicles]

@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    data: VehicleCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    vehicle = vehicle_service.create_vehicle(db, data, admin.id)
    return populate_vehicle_response(db, vehicle)

@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    vehicle = vehicle_service.get_vehicle_by_id(db, vehicle_id)
    
    # Permission check for driver
    if current_user.role == UserRole.DRIVER:
        assigned = vehicle_service.get_driver_assigned_vehicles(db, current_user.id)
        if vehicle.id not in [v.id for v in assigned]:
            raise PermissionDeniedException("Access denied: You are not assigned to this vehicle")
            
    return populate_vehicle_response(db, vehicle)

@router.patch("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_id: int,
    data: VehicleUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    vehicle = vehicle_service.update_vehicle(db, vehicle_id, data, admin.id)
    return populate_vehicle_response(db, vehicle)

@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    vehicle_service.delete_vehicle(db, vehicle_id, admin.id)

@router.post("/{vehicle_id}/assign", status_code=status.HTTP_200_OK)
def assign_driver_to_vehicle(
    vehicle_id: int,
    data: VehicleAssignRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    assignment = vehicle_service.assign_driver(db, vehicle_id, data.driver_id, admin.id)
    return {"message": "Driver assigned successfully", "assignment_id": assignment.id}
