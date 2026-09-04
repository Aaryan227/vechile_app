from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.db.models.tax import TaxType, ChargeType, TaxStatus, ChallanStatus, FASTagStatus

# --- Vehicle Taxes ---
class TaxRecordBase(BaseModel):
    tax_type: TaxType
    state: str = Field(..., max_length=50)
    tax_authority: Optional[str] = Field(None, max_length=100)
    period_start: date
    period_end: date
    amount: float = Field(..., ge=0)
    payment_date: Optional[date] = None
    due_date: Optional[date] = None
    valid_from: Optional[date] = None
    valid_until: date
    payment_reference: Optional[str] = Field(None, max_length=100)
    challan_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None

class TaxRecordCreate(TaxRecordBase):
    pass

class TaxRecordUpdate(BaseModel):
    tax_type: Optional[TaxType] = None
    state: Optional[str] = None
    tax_authority: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    amount: Optional[float] = Field(None, ge=0)
    payment_date: Optional[date] = None
    due_date: Optional[date] = None
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    payment_reference: Optional[str] = None
    challan_number: Optional[str] = None
    notes: Optional[str] = None

class TaxRecordResponse(TaxRecordBase):
    id: int
    vehicle_id: int
    status: TaxStatus
    receipt_file_url: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Government Charges ---
class GovernmentChargeBase(BaseModel):
    charge_type: ChargeType
    state: str = Field(..., max_length=50)
    authority: Optional[str] = Field(None, max_length=100)
    period_start: date
    period_end: date
    amount: float = Field(..., ge=0)
    payment_date: Optional[date] = None
    due_date: Optional[date] = None
    valid_from: Optional[date] = None
    valid_until: date
    payment_reference: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None

class GovernmentChargeCreate(GovernmentChargeBase):
    pass

class GovernmentChargeUpdate(BaseModel):
    charge_type: Optional[ChargeType] = None
    state: Optional[str] = None
    authority: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    amount: Optional[float] = Field(None, ge=0)
    payment_date: Optional[date] = None
    due_date: Optional[date] = None
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None

class GovernmentChargeResponse(GovernmentChargeBase):
    id: int
    vehicle_id: int
    status: TaxStatus
    receipt_file_url: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Challans / Penalties ---
class ChallanBase(BaseModel):
    challan_number: str = Field(..., max_length=100)
    authority: Optional[str] = Field(None, max_length=100)
    reason: Optional[str] = Field(None, max_length=255)
    issue_date: date
    amount: float = Field(..., ge=0)
    due_date: Optional[date] = None
    payment_date: Optional[date] = None
    status: ChallanStatus = ChallanStatus.UNPAID
    notes: Optional[str] = None

class ChallanCreate(ChallanBase):
    pass

class ChallanUpdate(BaseModel):
    challan_number: Optional[str] = None
    authority: Optional[str] = None
    reason: Optional[str] = None
    issue_date: Optional[date] = None
    amount: Optional[float] = Field(None, ge=0)
    due_date: Optional[date] = None
    payment_date: Optional[date] = None
    status: Optional[ChallanStatus] = None
    notes: Optional[str] = None

class ChallanResponse(ChallanBase):
    id: int
    vehicle_id: int
    receipt_file_url: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- FASTag Subsection ---
class FASTagBase(BaseModel):
    tag_number: Optional[str] = Field(None, max_length=100)
    tag_provider: Optional[str] = Field(None, max_length=100)
    tag_status: FASTagStatus = FASTagStatus.ACTIVE
    linked_account_ref: Optional[str] = Field(None, max_length=100)
    last_balance: Optional[float] = None
    notes: Optional[str] = None

class FASTagUpdate(FASTagBase):
    pass

class FASTagResponse(FASTagBase):
    id: int
    vehicle_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Dashboard / Compliance Summary ---
class TaxComplianceSummaryResponse(BaseModel):
    active_taxes: int = 0
    due_soon_taxes: int = 0
    overdue_taxes: int = 0
    expired_taxes: int = 0
    unpaid_challans: int = 0
