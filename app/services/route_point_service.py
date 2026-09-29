from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models.route_point import RoutePoint
from app.schemas.route_point import RoutePointCreate, RoutePointUpdate
from app.core.exceptions import NotFoundException, ConflictException

def get_or_create_route_point(db: Session, data: RoutePointCreate) -> RoutePoint:
    name_clean = data.name.strip()
    existing = db.query(RoutePoint).filter(RoutePoint.name.ilike(name_clean)).first()
    if existing:
        # If existing, update default RTKM/rate if provided
        if data.default_rtkm > 0:
            existing.default_rtkm = data.default_rtkm
        if data.default_rate > 0:
            existing.default_rate = data.default_rate
        if data.pump_station:
            existing.pump_station = data.pump_station
        existing.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing

    point = RoutePoint(
        name=name_clean,
        point_type=data.point_type,
        default_rtkm=data.default_rtkm,
        default_rate=data.default_rate,
        pump_station=data.pump_station.strip() if data.pump_station else None
    )
    db.add(point)
    db.commit()
    db.refresh(point)
    return point

def get_route_points(db: Session, point_type: Optional[str] = None) -> List[RoutePoint]:
    query = db.query(RoutePoint)
    if point_type:
        query = query.filter(RoutePoint.point_type == point_type)
    return query.order_by(RoutePoint.name.asc()).all()

def get_route_point_by_name(db: Session, name: str) -> Optional[RoutePoint]:
    return db.query(RoutePoint).filter(RoutePoint.name.ilike(name.strip())).first()

def update_route_point(db: Session, point_id: int, data: RoutePointUpdate) -> RoutePoint:
    point = db.query(RoutePoint).filter(RoutePoint.id == point_id).first()
    if not point:
        raise NotFoundException("Route point not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(point, field, val)

    point.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(point)
    return point
