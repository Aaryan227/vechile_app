from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.schemas.user import UserResponse

class VehicleBase(BaseModel):
    vehicle_number: str
    vehicle_class: str = "Tanker"
    make: Optional[str] = None
    model: Optional[str] = None
    manufacture_year: Optional[int] = None
    chassis_number: Optional[str] = None
    engine_number: Optional[str] = None
    status: str = "ACTIVE"

class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(BaseModel):
    vehicle_number: Optional[str] = None
    vehicle_class: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    manufacture_year: Optional[int] = None
    chassis_number: Optional[str] = None
    engine_number: Optional[str] = None
    status: Optional[str] = None

class VehicleAssignRequest(BaseModel):
    driver_id: int

class VehicleResponse(VehicleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    active_driver: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)
