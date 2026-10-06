from datetime import date, datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models.expense import VehicleExpense, ExpenseCategory
from app.db.models.vehicle import Vehicle
from app.db.models.tax import VehicleFASTag, FASTagStatus
from app.db.models.tanker_report import TankerDailyReport
from app.db.models.audit_log import AuditLog
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.core.exceptions import NotFoundException, BadRequestException

def create_expense(db: Session, data: ExpenseCreate, user_id: int) -> VehicleExpense:
    vehicle = db.query(Vehicle).filter(Vehicle.id == data.vehicle_id).first()
    if not vehicle:
        raise NotFoundException("Vehicle not found")

    if data.trip_id:
        trip = db.query(TankerDailyReport).filter(TankerDailyReport.id == data.trip_id).first()
        if not trip:
            raise NotFoundException("Specified trip report not found")

    expense = VehicleExpense(
        vehicle_id=data.vehicle_id,
        expense_date=data.expense_date,
        trip_id=data.trip_id,
        category=data.category,
        amount=data.amount,
        description=data.description.strip() if data.description else None,
        vendor_name=data.vendor_name.strip() if data.vendor_name else None,
        receipt_url=data.receipt_url.strip() if data.receipt_url else None,
        created_by=user_id
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)

    fastag_warning = None
    fastag_balance = None

    # Auto-deduct from FASTag if category is TOLL
    if expense.category == ExpenseCategory.TOLL:
        fastag = db.query(VehicleFASTag).filter(VehicleFASTag.vehicle_id == expense.vehicle_id).first()
        if fastag and fastag.last_balance is not None:
            old_balance = fastag.last_balance
            new_balance = round(old_balance - expense.amount, 2)
            fastag.last_balance = new_balance
            fastag_balance = new_balance

            if new_balance <= 0:
                fastag.tag_status = FASTagStatus.LOW_BALANCE
                fastag_warning = (
                    f"⚠️ Warning: FASTag balance surpassed for vehicle {vehicle.vehicle_number}! "
                    f"Previous balance: ₹{old_balance:,.2f}, Toll deducted: ₹{expense.amount:,.2f}, "
                    f"Remaining balance: ₹{new_balance:,.2f}. Status marked as LOW BALANCE. Please recharge."
                )

            fastag.updated_at = datetime.now(timezone.utc)
            db.commit()

    expense.fastag_balance = fastag_balance
    expense.fastag_warning = fastag_warning

    audit_details = f"Logged {expense.category} expense of ₹{expense.amount} for vehicle {vehicle.vehicle_number}"
    if fastag_warning:
        audit_details += f". FASTag deficit alert: remaining balance ₹{fastag_balance:,.2f}"

    audit = AuditLog(
        user_id=user_id,
        action="CREATE_EXPENSE",
        entity_type="expense",
        entity_id=expense.id,
        details=audit_details
    )
    db.add(audit)
    db.commit()
    return expense

def get_expenses(
    db: Session,
    skip: int = 0,
    limit: int = 200,
    vehicle_id: Optional[int] = None,
    category: Optional[ExpenseCategory] = None,
    trip_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None
) -> List[VehicleExpense]:
    query = db.query(VehicleExpense)

    if vehicle_id:
        query = query.filter(VehicleExpense.vehicle_id == vehicle_id)
    if category:
        query = query.filter(VehicleExpense.category == category)
    if trip_id:
        query = query.filter(VehicleExpense.trip_id == trip_id)
    if date_from:
        query = query.filter(VehicleExpense.expense_date >= date_from)
    if date_to:
        query = query.filter(VehicleExpense.expense_date <= date_to)

    return query.order_by(VehicleExpense.expense_date.desc(), VehicleExpense.id.desc()).offset(skip).limit(limit).all()

def get_expense_by_id(db: Session, expense_id: int) -> VehicleExpense:
    expense = db.query(VehicleExpense).filter(VehicleExpense.id == expense_id).first()
    if not expense:
        raise NotFoundException("Expense entry not found")
    return expense

def update_expense(db: Session, expense_id: int, data: ExpenseUpdate, user_id: int) -> VehicleExpense:
    expense = get_expense_by_id(db, expense_id)
    update_data = data.model_dump(exclude_unset=True)

    old_vehicle_id = expense.vehicle_id
    old_category = expense.category
    old_amount = expense.amount

    if "vehicle_id" in update_data and update_data["vehicle_id"]:
        vehicle = db.query(Vehicle).filter(Vehicle.id == update_data["vehicle_id"]).first()
        if not vehicle:
            raise NotFoundException("Vehicle not found")

    for field, val in update_data.items():
        setattr(expense, field, val)

    expense.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(expense)

    fastag_warning = None
    fastag_balance = None

    # Handle FASTag balance adjustment if category was or became TOLL
    if old_category == ExpenseCategory.TOLL or expense.category == ExpenseCategory.TOLL:
        if old_vehicle_id == expense.vehicle_id:
            fastag = db.query(VehicleFASTag).filter(VehicleFASTag.vehicle_id == expense.vehicle_id).first()
            if fastag and fastag.last_balance is not None:
                if old_category == ExpenseCategory.TOLL and expense.category == ExpenseCategory.TOLL:
                    diff = old_amount - expense.amount
                    fastag.last_balance = round(fastag.last_balance + diff, 2)
                elif old_category == ExpenseCategory.TOLL and expense.category != ExpenseCategory.TOLL:
                    fastag.last_balance = round(fastag.last_balance + old_amount, 2)
                elif old_category != ExpenseCategory.TOLL and expense.category == ExpenseCategory.TOLL:
                    fastag.last_balance = round(fastag.last_balance - expense.amount, 2)

                if fastag.last_balance <= 0:
                    fastag.tag_status = FASTagStatus.LOW_BALANCE
                    fastag_warning = (
                        f"⚠️ Warning: FASTag balance surpassed! Remaining balance: ₹{fastag.last_balance:,.2f}. "
                        f"Status marked as LOW BALANCE. Please recharge."
                    )
                elif fastag.tag_status == FASTagStatus.LOW_BALANCE and fastag.last_balance > 0:
                    fastag.tag_status = FASTagStatus.ACTIVE

                fastag.updated_at = datetime.now(timezone.utc)
                fastag_balance = fastag.last_balance
                db.commit()
        else:
            if old_category == ExpenseCategory.TOLL:
                old_fastag = db.query(VehicleFASTag).filter(VehicleFASTag.vehicle_id == old_vehicle_id).first()
                if old_fastag and old_fastag.last_balance is not None:
                    old_fastag.last_balance = round(old_fastag.last_balance + old_amount, 2)
                    if old_fastag.last_balance > 0 and old_fastag.tag_status == FASTagStatus.LOW_BALANCE:
                        old_fastag.tag_status = FASTagStatus.ACTIVE
                    old_fastag.updated_at = datetime.now(timezone.utc)

            if expense.category == ExpenseCategory.TOLL:
                new_fastag = db.query(VehicleFASTag).filter(VehicleFASTag.vehicle_id == expense.vehicle_id).first()
                if new_fastag and new_fastag.last_balance is not None:
                    new_fastag.last_balance = round(new_fastag.last_balance - expense.amount, 2)
                    if new_fastag.last_balance <= 0:
                        new_fastag.tag_status = FASTagStatus.LOW_BALANCE
                        fastag_warning = (
                            f"⚠️ Warning: FASTag balance surpassed! Remaining balance: ₹{new_fastag.last_balance:,.2f}. "
                            f"Status marked as LOW BALANCE. Please recharge."
                        )
                    elif new_fastag.tag_status == FASTagStatus.LOW_BALANCE and new_fastag.last_balance > 0:
                        new_fastag.tag_status = FASTagStatus.ACTIVE
                    new_fastag.updated_at = datetime.now(timezone.utc)
                    fastag_balance = new_fastag.last_balance

            db.commit()

    expense.fastag_balance = fastag_balance
    expense.fastag_warning = fastag_warning

    audit = AuditLog(user_id=user_id, action="UPDATE_EXPENSE", entity_type="expense", entity_id=expense.id)
    db.add(audit)
    db.commit()
    return expense

def delete_expense(db: Session, expense_id: int, user_id: int) -> None:
    expense = get_expense_by_id(db, expense_id)

    # Revert FASTag deduction if toll expense is deleted
    if expense.category == ExpenseCategory.TOLL:
        fastag = db.query(VehicleFASTag).filter(VehicleFASTag.vehicle_id == expense.vehicle_id).first()
        if fastag and fastag.last_balance is not None:
            fastag.last_balance = round(fastag.last_balance + expense.amount, 2)
            if fastag.last_balance > 0 and fastag.tag_status == FASTagStatus.LOW_BALANCE:
                fastag.tag_status = FASTagStatus.ACTIVE
            fastag.updated_at = datetime.now(timezone.utc)

    db.delete(expense)
    db.commit()

    audit = AuditLog(user_id=user_id, action="DELETE_EXPENSE", entity_type="expense", entity_id=expense_id)
    db.add(audit)
    db.commit()

