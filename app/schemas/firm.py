from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class FirmBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    registration_number: Optional[str] = Field(None, max_length=50)
    contact_person: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    is_active: bool = True

class FirmCreate(FirmBase):
    pass

class FirmUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    registration_number: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None

class FirmResponse(FirmBase):
    id: int
    created_at: datetime
    updated_at: datetime
    vehicle_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)
