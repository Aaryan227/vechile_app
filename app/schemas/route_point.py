from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

class RoutePointBase(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    point_name: Optional[str] = None
    point_type: str = "UNLOADING"  # LOADING, UNLOADING, BOTH
    default_rtkm: float = Field(0.0, ge=0.0)
    default_rate: float = Field(0.0, ge=0.0)
    pump_station: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def unify_name(cls, data):
        if isinstance(data, dict):
            if "point_name" in data and not data.get("name"):
                data["name"] = data["point_name"]
            elif "name" in data and not data.get("point_name"):
                data["point_name"] = data["name"]
        return data

class RoutePointCreate(RoutePointBase):
    @model_validator(mode="after")
    def check_required_name(self):
        if not self.name and not self.point_name:
            raise ValueError("Point name is required")
        if not self.name:
            self.name = self.point_name
        return self

class RoutePointUpdate(BaseModel):
    name: Optional[str] = None
    point_name: Optional[str] = None
    point_type: Optional[str] = None
    default_rtkm: Optional[float] = None
    default_rate: Optional[float] = None
    pump_station: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def unify_name(cls, data):
        if isinstance(data, dict):
            if "point_name" in data and not data.get("name"):
                data["name"] = data["point_name"]
        return data

class RoutePointResponse(RoutePointBase):
    id: int
    name: str
    point_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def set_point_name(self):
        if not self.point_name and self.name:
            self.point_name = self.name
        return self
