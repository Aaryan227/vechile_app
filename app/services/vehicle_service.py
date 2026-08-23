from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models.vehicle import Vehicle
from app.db.models.vehicle_assignment import VehicleAssignment
from app.db.models.user import User, UserRole
from app.db.models.audit_log import AuditLog
from app.schemas.vehicle import VehicleCreate, VehicleUpdate
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException

def create_vehicle(db: Session, data: VehicleCreate, admin_id: int) -> Vehicle:
    if db.query(Vehicle).filter(Vehicle.vehicle_number == data.vehicle_number).first():
        raise ConflictException(f"Vehicle with number {data.vehicle_number} already exists")
    
    vehicle = Vehicle(**data.model_dump())
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    
    audit = AuditLog(user_id=admin_id, action="CREATE_VEHICLE", entity_type="vehicle", entity_id=vehicle.id)
    db.add(audit)
    db.commit()
    return vehicle

def get_vehicles(db: Session, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[Vehicle]:
    query = db.query(Vehicle)
    if status:
        query = query.filter(Vehicle.status == status)
    return query.offset(skip).limit(limit).all()

def get_vehicle_by_id(db: Session, vehicle_id: int) -> Vehicle:
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise NotFoundException("Vehicle not found")
    return vehicle

def update_vehicle(db: Session, vehicle_id: int, data: VehicleUpdate, admin_id: int) -> Vehicle:
    vehicle = get_vehicle_by_id(db, vehicle_id)
    update_data = data.model_dump(exclude_unset=True)
    
    if "vehicle_number" in update_data and update_data["vehicle_number"] != vehicle.vehicle_number:
        if db.query(Vehicle).filter(Vehicle.vehicle_number == update_data["vehicle_number"]).first():
            raise ConflictException(f"Vehicle number {update_data['vehicle_number']} already in use")
            
    for key, value in update_data.items():
        setattr(vehicle, key, value)
        
    db.commit()
    db.refresh(vehicle)
    
    audit = AuditLog(user_id=admin_id, action="UPDATE_VEHICLE", entity_type="vehicle", entity_id=vehicle.id)
    db.add(audit)
    db.commit()
    return vehicle

def delete_vehicle(db: Session, vehicle_id: int, admin_id: int) -> None:
    vehicle = get_vehicle_by_id(db, vehicle_id)
    db.delete(vehicle)
    db.commit()
    
    audit = AuditLog(user_id=admin_id, action="DELETE_VEHICLE", entity_type="vehicle", entity_id=vehicle_id)
    db.add(audit)
    db.commit()

def assign_driver(db: Session, vehicle_id: int, driver_id: int, admin_id: int) -> VehicleAssignment:
    vehicle = get_vehicle_by_id(db, vehicle_id)
    driver = db.query(User).filter(User.id == driver_id, User.role == UserRole.DRIVER).first()
    if not driver:
        raise NotFoundException("Driver not found")
        
    # Deactivate previous active assignments for this vehicle
    active_assignments = db.query(VehicleAssignment).filter(
        VehicleAssignment.vehicle_id == vehicle_id,
        VehicleAssignment.is_active == True
    ).all()
    
    for assign in active_assignments:
        assign.is_active = False
        assign.assigned_to = datetime.now(timezone.utc)
        
    new_assignment = VehicleAssignment(
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        assigned_from=datetime.now(timezone.utc),
        is_active=True
    )
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)
    
    audit = AuditLog(
        user_id=admin_id,
        action="ASSIGN_VEHICLE",
        entity_type="vehicle_assignment",
        entity_id=new_assignment.id,
        details=f"Assigned vehicle {vehicle.vehicle_number} to driver {driver.name}"
    )
    db.add(audit)
    db.commit()
    return new_assignment

def get_active_driver_for_vehicle(db: Session, vehicle_id: int) -> Optional[User]:
    assignment = db.query(VehicleAssignment).filter(
        VehicleAssignment.vehicle_id == vehicle_id,
        VehicleAssignment.is_active == True
    ).first()
    if assignment:
        return assignment.driver
    return None

def get_driver_assigned_vehicles(db: Session, driver_id: int) -> List[Vehicle]:
    assignments = db.query(VehicleAssignment).filter(
        VehicleAssignment.driver_id == driver_id,
        VehicleAssignment.is_active == True
    ).all()
    return [assign.vehicle for assign in assignments]
