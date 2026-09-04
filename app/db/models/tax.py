import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, ForeignKey, Float, Text, CheckConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base

class TaxType(str, enum.Enum):
    ROAD_TAX = "ROAD_TAX"
    MOTOR_VEHICLE_TAX = "MOTOR_VEHICLE_TAX"
    ADDITIONAL_MOTOR_VEHICLE_TAX = "ADDITIONAL_MOTOR_VEHICLE_TAX"
    STATE_VEHICLE_TAX = "STATE_VEHICLE_TAX"
    OTHER_TAX = "OTHER_TAX"

class ChargeType(str, enum.Enum):
    PERMIT_FEE = "PERMIT_FEE"
    NATIONAL_PERMIT_FEE = "NATIONAL_PERMIT_FEE"
    STATE_PERMIT_FEE = "STATE_PERMIT_FEE"
    OTHER_GOVERNMENT_CHARGE = "OTHER_GOVERNMENT_CHARGE"

class TaxStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DUE_SOON = "DUE_SOON"
    OVERDUE = "OVERDUE"
    EXPIRED = "EXPIRED"
    PENDING = "PENDING"

class ChallanStatus(str, enum.Enum):
    UNPAID = "UNPAID"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    DISPUTED = "DISPUTED"

class FASTagStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    LOW_BALANCE = "LOW_BALANCE"
    SUSPENDED = "SUSPENDED"
    INACTIVE = "INACTIVE"

class VehicleTaxRecord(Base):
    __tablename__ = "vehicle_tax_records"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    tax_type = Column(Enum(TaxType), nullable=False, index=True)
    state = Column(String(50), nullable=False, index=True)
    tax_authority = Column(String(100), nullable=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True, index=True)
    valid_from = Column(Date, nullable=True)
    valid_until = Column(Date, nullable=False, index=True)
    status = Column(Enum(TaxStatus), nullable=False, default=TaxStatus.ACTIVE, index=True)
    payment_reference = Column(String(100), nullable=True)
    challan_number = Column(String(100), nullable=True)
    receipt_file_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    vehicle = relationship("Vehicle", back_populates="tax_records")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        CheckConstraint("amount >= 0", name="check_tax_amount_non_negative"),
        CheckConstraint("period_end >= period_start", name="check_tax_period_valid"),
        CheckConstraint("valid_until >= valid_from", name="check_tax_validity_valid"),
    )


class VehicleGovernmentCharge(Base):
    __tablename__ = "vehicle_government_charges"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    charge_type = Column(Enum(ChargeType), nullable=False, index=True)
    state = Column(String(50), nullable=False, index=True)
    authority = Column(String(100), nullable=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True, index=True)
    valid_from = Column(Date, nullable=True)
    valid_until = Column(Date, nullable=False, index=True)
    status = Column(Enum(TaxStatus), nullable=False, default=TaxStatus.ACTIVE, index=True)
    payment_reference = Column(String(100), nullable=True)
    receipt_file_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    vehicle = relationship("Vehicle", back_populates="government_charges")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        CheckConstraint("amount >= 0", name="check_charge_amount_non_negative"),
        CheckConstraint("period_end >= period_start", name="check_charge_period_valid"),
        CheckConstraint("valid_until >= valid_from", name="check_charge_validity_valid"),
    )


class VehicleChallan(Base):
    __tablename__ = "vehicle_challans"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    challan_number = Column(String(100), nullable=False, index=True)
    authority = Column(String(100), nullable=True)
    reason = Column(String(255), nullable=True)
    issue_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    due_date = Column(Date, nullable=True)
    payment_date = Column(Date, nullable=True)
    status = Column(Enum(ChallanStatus), nullable=False, default=ChallanStatus.UNPAID, index=True)
    receipt_file_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    vehicle = relationship("Vehicle", back_populates="challans")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        CheckConstraint("amount >= 0", name="check_challan_amount_non_negative"),
    )


class VehicleFASTag(Base):
    __tablename__ = "vehicle_fastags"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    tag_number = Column(String(100), nullable=True)
    tag_provider = Column(String(100), nullable=True)
    tag_status = Column(Enum(FASTagStatus), nullable=False, default=FASTagStatus.ACTIVE)
    linked_account_ref = Column(String(100), nullable=True)
    last_balance = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    vehicle = relationship("Vehicle", back_populates="fastag")
