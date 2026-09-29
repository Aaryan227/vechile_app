from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.core.dependencies import get_current_user
from app.schemas.financial import ProfitLossResponse, LogBookResponse
from app.services import financial_service, export_service

router = APIRouter(prefix="/financials", tags=["Financials & Log Book"])

@router.get("/profit-loss", response_model=ProfitLossResponse)
def get_profit_and_loss(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    vehicle_id: Optional[int] = None,
    firm_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return financial_service.get_profit_loss_summary(
        db, date_from=date_from, date_to=date_to, vehicle_id=vehicle_id, firm_id=firm_id
    )

@router.get("/log-book", response_model=LogBookResponse)
def get_financial_log_book(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    vehicle_id: Optional[int] = None,
    firm_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return financial_service.get_log_book(
        db, date_from=date_from, date_to=date_to, vehicle_id=vehicle_id, firm_id=firm_id
    )

@router.get("/export")
def export_financial_log_book(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    vehicle_id: Optional[int] = None,
    firm_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    log_book = financial_service.get_log_book(
        db, date_from=date_from, date_to=date_to, vehicle_id=vehicle_id, firm_id=firm_id
    )
    excel_stream = export_service.export_log_book_to_excel(log_book.summary, log_book.entries)

    filename = f"Log_Book_{date_from or 'all'}_to_{date_to or 'all'}.xlsx"
    headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
    return StreamingResponse(
        excel_stream,
        headers=headers,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
