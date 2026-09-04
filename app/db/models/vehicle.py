from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_number = Column(String(50), unique=True, index=True, nullable=False)
    vehicle_class = Column(String(50), nullable=False, default="Tanker")
    make = Column(String(50), nullable=True)
    model = Column(String(50), nullable=True)
    manufacture_year = Column(Integer, nullable=True)
    chassis_number = Column(String(100), nullable=True)
    engine_number = Column(String(100), nullable=True)
    status = Column(String(20), default="ACTIVE", nullable=False)  # ACTIVE, INACTIVE, MAINTENANCE
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    assignments = relationship("VehicleAssignment", back_populates="vehicle", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="vehicle", cascade="all, delete-orphan")
    tanker_reports = relationship("TankerDailyReport", back_populates="vehicle", cascade="all, delete-orphan")
    tax_records = relationship("VehicleTaxRecord", back_populates="vehicle", cascade="all, delete-orphan")
    government_charges = relationship("VehicleGovernmentCharge", back_populates="vehicle", cascade="all, delete-orphan")
    challans = relationship("VehicleChallan", back_populates="vehicle", cascade="all, delete-orphan")
    fastag = relationship("VehicleFASTag", back_populates="vehicle", uselist=False, cascade="all, delete-orphan")
