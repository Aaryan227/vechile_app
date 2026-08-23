from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.user import User, UserRole
from app.core.dependencies import get_current_user
from app.schemas.tanker_report import TankerReportCreate, TankerReportUpdate, TankerReportResponse
from app.services import tanker_report_service, export_service, vehicle_service
from app.core.exceptions import PermissionDeniedException, NotFoundException

router = APIRouter(prefix="/tanker-reports", tags=["Tanker Daily Reports"])

def populate_tanker_response(db: Session, report) -> TankerReportResponse:
    res = TankerReportResponse.model_validate(report)
    if report.vehicle:
        res.vehicle_number = report.vehicle.vehicle_number
    if report.driver:
        res.driver_name = report.driver.name
    return res

@router.post("", response_model=TankerReportResponse, status_code=status.HTTP_201_CREATED)
def create_tanker_report(
    data: TankerReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Driver permission check
    if current_user.role == UserRole.DRIVER:
        assigned = vehicle_service.get_driver_assigned_vehicles(db, current_user.id)
        if data.vehicle_id not in [v.id for v in assigned]:
            raise PermissionDeniedException("You can only submit reports for assigned vehicles")
        if data.driver_id is None:
            data.driver_id = current_user.id
            
    report = tanker_report_service.create_tanker_report(db, data, current_user.id)
    return populate_tanker_response(db, report)

@router.get("/export")
def export_tanker_reports(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000, le=2100),
    vehicle_id: Optional[int] = None,
    ul_point: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    reports = tanker_report_service.get_tanker_reports(
        db, skip=0, limit=10000, month=month, year=year, vehicle_id=vehicle_id, ul_point=ul_point
    )
    excel_stream = export_service.export_tanker_reports_to_excel(reports)
    filename = f"Tanker_Daily_Report_{month or 'all'}_{year or 'all'}.xlsx"
    headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
    return StreamingResponse(
        excel_stream,
        headers=headers,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@router.get("", response_model=List[TankerReportResponse])
def list_tanker_reports(
    skip: int = 0,
    limit: int = 100,
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000, le=2100),
    vehicle_id: Optional[int] = None,
    driver_id: Optional[int] = None,
    ul_point: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.DRIVER:
        driver_id = current_user.id
        
    reports = tanker_report_service.get_tanker_reports(
        db, skip=skip, limit=limit, month=month, year=year,
        vehicle_id=vehicle_id, driver_id=driver_id, ul_point=ul_point,
        date_from=date_from, date_to=date_to
    )
    return [populate_tanker_response(db, r) for r in reports]

@router.get("/{report_id}", response_model=TankerReportResponse)
def get_tanker_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = tanker_report_service.get_tanker_report_by_id(db, report_id)
    if current_user.role == UserRole.DRIVER and report.driver_id != current_user.id:
        raise PermissionDeniedException("Access denied to this report entry")
    return populate_tanker_response(db, report)

@router.patch("/{report_id}", response_model=TankerReportResponse)
def update_tanker_report(
    report_id: int,
    data: TankerReportUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = tanker_report_service.get_tanker_report_by_id(db, report_id)
    if current_user.role == UserRole.DRIVER and report.driver_id != current_user.id:
        raise PermissionDeniedException("Access denied to update this report entry")
    updated = tanker_report_service.update_tanker_report(db, report_id, data, current_user.id)
    return populate_tanker_response(db, updated)

@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tanker_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = tanker_report_service.get_tanker_report_by_id(db, report_id)
    if current_user.role == UserRole.DRIVER and report.driver_id != current_user.id:
        raise PermissionDeniedException("Access denied to delete this report entry")
    tanker_report_service.delete_tanker_report(db, report_id, current_user.id)
