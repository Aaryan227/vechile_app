from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.db.session import Base

class RoutePoint(Base):
    __tablename__ = "route_points"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), unique=True, nullable=False, index=True)
    point_type = Column(String(50), default="UNLOADING", nullable=False)  # LOADING, UNLOADING, BOTH
    default_rtkm = Column(Float, default=0.0, nullable=False)
    default_rate = Column(Float, default=0.0, nullable=False)
    pump_station = Column(String(150), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
