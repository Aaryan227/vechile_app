import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class ExpenseCategory(str, enum.Enum):
    TYRE = "tyre"
    BATTERY = "battery"
    MAINTENANCE = "maintenance"
    SALARY = "salary"
    KHURAKI = "khuraki"
    TOLL = "toll"
    ROAD_TAX = "road_tax"
    OTHERS = "others"

class VehicleExpense(Base):
    __tablename__ = "vehicle_expenses"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    expense_date = Column(Date, nullable=False, index=True)
    trip_id = Column(Integer, ForeignKey("tanker_reports.id", ondelete="SET NULL"), nullable=True, index=True)
    category = Column(Enum(ExpenseCategory, native_enum=False), nullable=False, index=True)
    amount = Column(Float, nullable=False, default=0.0)
    description = Column(String(255), nullable=True)
    vendor_name = Column(String(150), nullable=True)
    receipt_url = Column(String(500), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    vehicle = relationship("Vehicle", back_populates="expenses")
    trip = relationship("TankerDailyReport")
