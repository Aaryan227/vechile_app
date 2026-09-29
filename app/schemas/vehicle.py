from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.user import UserResponse

class VehicleBase(BaseModel):
    vehicle_number: str
    vehicle_class: str = "Tanker"
    firm_id: Optional[int] = None
    make: Optional[str] = None
    model: Optional[str] = None
    manufacture_year: Optional[int] = None
    chassis_number: Optional[str] = None
    engine_number: Optional[str] = None
    status: str = "ACTIVE"

class VehicleCreate(VehicleBase):
    firm_id: int = Field(..., description="Firm ID is compulsory before adding a vehicle")

class VehicleUpdate(BaseModel):
    vehicle_number: Optional[str] = None
    vehicle_class: Optional[str] = None
    firm_id: Optional[int] = None
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
    firm_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    active_driver: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)
