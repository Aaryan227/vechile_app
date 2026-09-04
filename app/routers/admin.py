from datetime import date, datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.db.session import get_db
from app.db.models.user import User, UserRole
from app.db.models.vehicle import Vehicle
from app.db.models.document import Document, DocumentStatus
from app.db.models.tanker_report import TankerDailyReport
from app.db.models.tax import TaxStatus
from app.core.dependencies import get_current_admin
from app.schemas.report import DashboardMetricsResponse
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.auth import AdminUserCreate
from app.schemas.tax import TaxRecordResponse
from app.services import auth_service, document_service, tax_service, export_service
from app.core.exceptions import NotFoundException, BadRequestException

router = APIRouter(prefix="/admin", tags=["Admin Operations"])

@router.get("/dashboard", response_model=DashboardMetricsResponse)
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    today = date.today()
    current_month = today.month
    current_year = today.year
    
    total_vehicles = db.query(Vehicle).count()
    active_vehicles = db.query(Vehicle).filter(Vehicle.status == "ACTIVE").count()
    total_drivers = db.query(User).filter(User.role == UserRole.DRIVER).count()
    
    expired_docs = len(document_service.get_expired_documents(db))
    expiring_soon_docs = len(document_service.get_expiring_soon_documents(db, days=30))
    
    monthly_tanker_query = db.query(TankerDailyReport).filter(
        extract('month', TankerDailyReport.report_date) == current_month,
        extract('year', TankerDailyReport.report_date) == current_year
    )
    total_entries = monthly_tanker_query.count()
    total_freight = db.query(func.sum(TankerDailyReport.freight)).filter(
        extract('month', TankerDailyReport.report_date) == current_month,
        extract('year', TankerDailyReport.report_date) == current_year
    ).scalar() or 0.0

    tax_summary = tax_service.get_tax_compliance_summary(db)

    return DashboardMetricsResponse(
        total_vehicles=total_vehicles,
        active_vehicles=active_vehicles,
        total_drivers=total_drivers,
        expired_documents=expired_docs,
        documents_expiring_soon=expiring_soon_docs,
        total_tanker_entries_this_month=total_entries,
        total_freight_this_month=round(float(total_freight), 2),
        active_taxes=tax_summary["active_taxes"],
        taxes_due_soon=tax_summary["due_soon_taxes"],
        taxes_overdue=tax_summary["overdue_taxes"],
        taxes_expired=tax_summary["expired_taxes"]
    )

@router.get("/drivers", response_model=List[UserResponse])
def get_all_drivers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    return db.query(User).filter(User.role == UserRole.DRIVER).offset(skip).limit(limit).all()

@router.post("/drivers", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_driver(
    data: AdminUserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    data.role = UserRole.DRIVER
    return auth_service.create_user_by_admin(db, data, admin.id)

@router.patch("/drivers/{driver_id}", response_model=UserResponse)
def update_driver(
    driver_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    driver = db.query(User).filter(User.id == driver_id, User.role == UserRole.DRIVER).first()
    if not driver:
        raise NotFoundException("Driver not found")
        
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(driver, k, v)
        
    db.commit()
    db.refresh(driver)
    return driver

@router.delete("/drivers/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    driver = db.query(User).filter(User.id == driver_id, User.role == UserRole.DRIVER).first()
    if not driver:
        raise NotFoundException("Driver not found")
        
    db.delete(driver)
    db.commit()


# ==========================================
# Fleet Taxes Management & Reporting (Admin)
# ==========================================

@router.get("/taxes", response_model=List[TaxRecordResponse])
def get_fleet_taxes(
    vehicle_id: Optional[int] = Query(None),
    tax_type: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    return tax_service.get_fleet_taxes(
        db, vehicle_id=vehicle_id, tax_type=tax_type, state=state,
        status=status, date_from=date_from, date_to=date_to, skip=skip, limit=limit
    )


@router.get("/taxes/due-soon", response_model=List[TaxRecordResponse])
def get_due_soon_taxes(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    return tax_service.get_taxes_by_status(db, TaxStatus.DUE_SOON)


@router.get("/taxes/overdue", response_model=List[TaxRecordResponse])
def get_overdue_taxes(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    return tax_service.get_taxes_by_status(db, TaxStatus.OVERDUE)


@router.get("/taxes/expired", response_model=List[TaxRecordResponse])
def get_expired_taxes(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    return tax_service.get_taxes_by_status(db, TaxStatus.EXPIRED)


@router.get("/taxes/export")
def export_taxes(
    vehicle_id: Optional[int] = Query(None),
    tax_type: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    taxes = tax_service.get_fleet_taxes(
        db, vehicle_id=vehicle_id, tax_type=tax_type, state=state, status=status, limit=10000
    )
    excel_stream = export_service.export_taxes_to_excel(taxes)
    filename = f"vehicle_taxes_export_{date.today().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
