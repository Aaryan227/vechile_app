from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.core.dependencies import get_current_user
from app.schemas.route_point import RoutePointCreate, RoutePointUpdate, RoutePointResponse
from app.services import route_point_service

router = APIRouter(prefix="/route-points", tags=["Route & Loading Points"])

@router.get("", response_model=List[RoutePointResponse])
def list_route_points(
    point_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    points = route_point_service.get_route_points(db, point_type=point_type)
    return [RoutePointResponse.model_validate(p) for p in points]

@router.post("", response_model=RoutePointResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_route_point(
    data: RoutePointCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    point = route_point_service.get_or_create_route_point(db, data)
    return RoutePointResponse.model_validate(point)

@router.patch("/{point_id}", response_model=RoutePointResponse)
def update_route_point(
    point_id: int,
    data: RoutePointUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    point = route_point_service.update_route_point(db, point_id, data)
    return RoutePointResponse.model_validate(point)
