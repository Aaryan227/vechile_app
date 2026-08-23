from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class TankerDailyReport(Base):
    __tablename__ = "tanker_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_date = Column(Date, nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    ul_point = Column(String(150), nullable=False, index=True)
    rtkm = Column(Float, nullable=False, default=0.0)
    rate = Column(Float, nullable=False, default=0.0)
    freight = Column(Float, nullable=False, default=0.0)
    pump = Column(String(150), nullable=True)
    hsd_ltr = Column(Float, nullable=False, default=0.0)
    hsd_rate = Column(Float, nullable=False, default=0.0)
    hsd_amount = Column(Float, nullable=False, default=0.0)
    khuraki = Column(Float, nullable=False, default=0.0)  # Ad hoc expense
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    vehicle = relationship("Vehicle", back_populates="tanker_reports")
    driver = relationship("User", foreign_keys=[driver_id], back_populates="tanker_reports")
