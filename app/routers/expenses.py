from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.expense import ExpenseCategory
from app.core.dependencies import get_current_user
from app.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseResponse
from app.services import expense_service

router = APIRouter(prefix="/expenses", tags=["Vehicle Expenses"])

def _populate_expense_response(expense) -> ExpenseResponse:
    res = ExpenseResponse.model_validate(expense)
    if expense.vehicle:
        res.vehicle_number = expense.vehicle.vehicle_number
        if expense.vehicle.firm:
            res.firm_name = expense.vehicle.firm.name
    return res

@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    expense = expense_service.create_expense(db, data, current_user.id)
    return _populate_expense_response(expense)

@router.get("", response_model=List[ExpenseResponse])
def list_expenses(
    skip: int = 0,
    limit: int = 200,
    vehicle_id: Optional[int] = None,
    category: Optional[ExpenseCategory] = None,
    trip_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    expenses = expense_service.get_expenses(
        db, skip=skip, limit=limit,
        vehicle_id=vehicle_id, category=category, trip_id=trip_id,
        date_from=date_from, date_to=date_to
    )
    return [_populate_expense_response(e) for e in expenses]

@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    expense = expense_service.get_expense_by_id(db, expense_id)
    return _populate_expense_response(expense)

@router.patch("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    updated = expense_service.update_expense(db, expense_id, data, current_user.id)
    return _populate_expense_response(updated)

@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    expense_service.delete_expense(db, expense_id, current_user.id)
