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


class NotificationItemResponse(BaseModel):
    id: int
    user_id: int
    title: str
    body: str
    notification_type: Optional[str] = None
    data_payload: Optional[dict] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationInboxResponse(BaseModel):
    unread_count: int
    total_count: int
    notifications: list[NotificationItemResponse]


class UnreadCountResponse(BaseModel):
    unread_count: int
