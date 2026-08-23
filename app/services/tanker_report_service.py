from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models.tanker_report import TankerDailyReport
from app.db.models.vehicle import Vehicle
from app.db.models.user import User
from app.db.models.audit_log import AuditLog
from app.schemas.tanker_report import TankerReportCreate, TankerReportUpdate
from app.core.exceptions import NotFoundException, BadRequestException

def calculate_tanker_fields(rtkm: float, rate: float, freight: Optional[float], hsd_ltr: float, hsd_rate: float, hsd_amount: Optional[float]) -> tuple[float, float]:
    calculated_freight = round(rtkm * rate, 2) if freight is None else freight
    calculated_hsd_amount = round(hsd_ltr * hsd_rate, 2) if hsd_amount is None else hsd_amount
    return calculated_freight, calculated_hsd_amount

def create_tanker_report(db: Session, data: TankerReportCreate, user_id: int) -> TankerDailyReport:
    vehicle = db.query(Vehicle).filter(Vehicle.id == data.vehicle_id).first()
    if not vehicle:
        raise NotFoundException("Specified vehicle not found")
        
    freight, hsd_amount = calculate_tanker_fields(
        data.rtkm, data.rate, data.freight,
        data.hsd_ltr, data.hsd_rate, data.hsd_amount
    )
    
    report = TankerDailyReport(
        report_date=data.report_date,
        vehicle_id=data.vehicle_id,
        driver_id=data.driver_id,
        ul_point=data.ul_point,
        rtkm=data.rtkm,
        rate=data.rate,
        freight=freight,
        pump=data.pump,
        hsd_ltr=data.hsd_ltr,
        hsd_rate=data.hsd_rate,
        hsd_amount=hsd_amount,
        khuraki=data.khuraki,
        created_by=user_id
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    audit = AuditLog(user_id=user_id, action="CREATE_TANKER_REPORT", entity_type="tanker_report", entity_id=report.id)
    db.add(audit)
    db.commit()
    return report

def get_tanker_reports(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    month: Optional[int] = None,
    year: Optional[int] = None,
    vehicle_id: Optional[int] = None,
    driver_id: Optional[int] = None,
    ul_point: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None
) -> List[TankerDailyReport]:
    query = db.query(TankerDailyReport)
    
    if month and year:
        from sqlalchemy import extract
        query = query.filter(
            extract('month', TankerDailyReport.report_date) == month,
            extract('year', TankerDailyReport.report_date) == year
        )
    elif year:
        from sqlalchemy import extract
        query = query.filter(extract('year', TankerDailyReport.report_date) == year)
        
    if vehicle_id:
        query = query.filter(TankerDailyReport.vehicle_id == vehicle_id)
        
    if driver_id:
        query = query.filter(TankerDailyReport.driver_id == driver_id)
        
    if ul_point:
        query = query.filter(TankerDailyReport.ul_point.ilike(f"%{ul_point}%"))
        
    if date_from:
        query = query.filter(TankerDailyReport.report_date >= date_from)
        
    if date_to:
        query = query.filter(TankerDailyReport.report_date <= date_to)
        
    return query.order_by(TankerDailyReport.report_date.desc()).offset(skip).limit(limit).all()

def get_tanker_report_by_id(db: Session, report_id: int) -> TankerDailyReport:
    report = db.query(TankerDailyReport).filter(TankerDailyReport.id == report_id).first()
    if not report:
        raise NotFoundException("Tanker report entry not found")
    return report

def update_tanker_report(db: Session, report_id: int, data: TankerReportUpdate, user_id: int) -> TankerDailyReport:
    report = get_tanker_report_by_id(db, report_id)
    update_data = data.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(report, key, value)
        
    # Re-calculate freight and hsd_amount if rtkm/rate or hsd_ltr/hsd_rate changed
    if "rtkm" in update_data or "rate" in update_data or "freight" in update_data:
        report.freight = round(report.rtkm * report.rate, 2) if "freight" not in update_data else report.freight
    if "hsd_ltr" in update_data or "hsd_rate" in update_data or "hsd_amount" in update_data:
        report.hsd_amount = round(report.hsd_ltr * report.hsd_rate, 2) if "hsd_amount" not in update_data else report.hsd_amount
        
    db.commit()
    db.refresh(report)
    
    audit = AuditLog(user_id=user_id, action="UPDATE_TANKER_REPORT", entity_type="tanker_report", entity_id=report.id)
    db.add(audit)
    db.commit()
    return report

def delete_tanker_report(db: Session, report_id: int, user_id: int) -> None:
    report = get_tanker_report_by_id(db, report_id)
    db.delete(report)
    db.commit()
    
    audit = AuditLog(user_id=user_id, action="DELETE_TANKER_REPORT", entity_type="tanker_report", entity_id=report_id)
    db.add(audit)
    db.commit()
