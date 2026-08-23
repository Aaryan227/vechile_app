from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class TankerReportBase(BaseModel):
    report_date: date
    vehicle_id: int
    driver_id: Optional[int] = None
    ul_point: str = Field(..., min_length=1, max_length=150)
    rtkm: float = 0.0
    rate: float = 0.0
    freight: Optional[float] = None
    pump: Optional[str] = None
    hsd_ltr: float = 0.0
    hsd_rate: float = 0.0
    hsd_amount: Optional[float] = None
    khuraki: float = 0.0

class TankerReportCreate(TankerReportBase):
    pass

class TankerReportUpdate(BaseModel):
    report_date: Optional[date] = None
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    ul_point: Optional[str] = None
    rtkm: Optional[float] = None
    rate: Optional[float] = None
    freight: Optional[float] = None
    pump: Optional[str] = None
    hsd_ltr: Optional[float] = None
    hsd_rate: Optional[float] = None
    hsd_amount: Optional[float] = None
    khuraki: Optional[float] = None

class TankerReportResponse(TankerReportBase):
    id: int
    freight: float
    hsd_amount: float
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    vehicle_number: Optional[str] = None
    driver_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
