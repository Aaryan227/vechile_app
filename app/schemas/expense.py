from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.db.models.expense import ExpenseCategory

class ExpenseBase(BaseModel):
    vehicle_id: int
    expense_date: date
    trip_id: Optional[int] = None
    category: ExpenseCategory
    amount: float = Field(..., gt=0.0)
    description: Optional[str] = Field(None, max_length=255)
    vendor_name: Optional[str] = Field(None, max_length=150)
    receipt_url: Optional[str] = Field(None, max_length=500)

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    vehicle_id: Optional[int] = None
    expense_date: Optional[date] = None
    trip_id: Optional[int] = None
    category: Optional[ExpenseCategory] = None
    amount: Optional[float] = Field(None, gt=0.0)
    description: Optional[str] = None
    vendor_name: Optional[str] = None
    receipt_url: Optional[str] = None

class ExpenseResponse(ExpenseBase):
    id: int
    vehicle_number: Optional[str] = None
    firm_name: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    fastag_balance: Optional[float] = None
    fastag_warning: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
