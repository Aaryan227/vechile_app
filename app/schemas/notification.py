from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class DeviceTokenCreate(BaseModel):
    device_token: str = Field(..., min_length=10, max_length=500)
    platform: Optional[str] = Field("android", max_length=20)

class DeviceTokenResponse(BaseModel):
    id: int
    user_id: int
    device_token: str
    platform: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
