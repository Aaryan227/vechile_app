from datetime import date
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models.tanker_report import TankerDailyReport
from app.db.models.expense import VehicleExpense, ExpenseCategory
from app.db.models.vehicle import Vehicle
from app.db.models.firm import Firm
from app.schemas.financial import ProfitLossResponse, CategorySummary, LogBookEntry, LogBookResponse

def get_profit_loss_summary(
    db: Session,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    vehicle_id: Optional[int] = None,
    firm_id: Optional[int] = None
) -> ProfitLossResponse:
    # 1. Query Trips for Income (Freight) and Trip Stats
    trip_query = db.query(TankerDailyReport)
    if date_from:
        trip_query = trip_query.filter(TankerDailyReport.report_date >= date_from)
    if date_to:
        trip_query = trip_query.filter(TankerDailyReport.report_date <= date_to)
    if vehicle_id:
        trip_query = trip_query.filter(TankerDailyReport.vehicle_id == vehicle_id)
    if firm_id:
        trip_query = trip_query.join(Vehicle, TankerDailyReport.vehicle_id == Vehicle.id).filter(Vehicle.firm_id == firm_id)

    trips = trip_query.all()
    total_income = round(sum(t.freight for t in trips), 2)
    total_rtkm = round(sum(t.rtkm for t in trips), 2)
    total_trips = len(trips)

    # 2. Query Expenses for Expenditure
    exp_query = db.query(VehicleExpense)
    if date_from:
        exp_query = exp_query.filter(VehicleExpense.expense_date >= date_from)
    if date_to:
        exp_query = exp_query.filter(VehicleExpense.expense_date <= date_to)
    if vehicle_id:
        exp_query = exp_query.filter(VehicleExpense.vehicle_id == vehicle_id)
    if firm_id:
        exp_query = exp_query.join(Vehicle, VehicleExpense.vehicle_id == Vehicle.id).filter(Vehicle.firm_id == firm_id)

    expenses = exp_query.all()
    total_logged_expenses = sum(e.amount for e in expenses)

    # Also calculate any trip-level diesel (HSD amount) if not logged separately in expense table
    # To prevent double counting, if an expense already exists with trip_id, it is part of expenses
    trip_hsd_total = sum(t.hsd_amount for t in trips if t.hsd_amount > 0)
    trip_khuraki_total = sum(t.khuraki for t in trips if t.khuraki > 0)

    # Category breakdown initialization for all 8 categories
    category_totals: Dict[str, float] = {cat.value: 0.0 for cat in ExpenseCategory}
    for e in expenses:
        cat_key = e.category.value if hasattr(e.category, "value") else str(e.category)
        if cat_key in category_totals:
            category_totals[cat_key] += e.amount
        else:
            category_totals[cat_key] = e.amount

    # If trip khuraki was entered on daily tanker entry but not as an expense record, incorporate it
    has_khuraki_expenses = category_totals.get("khuraki", 0.0) > 0
    if not has_khuraki_expenses and trip_khuraki_total > 0:
        category_totals["khuraki"] += round(trip_khuraki_total, 2)

    total_expenditure = round(sum(category_totals.values()), 2)
    net_profit = round(total_income - total_expenditure, 2)

    profit_margin = round((net_profit / total_income * 100), 2) if total_income > 0 else 0.0
    if net_profit > 0:
        profit_status = "PROFIT"
    elif net_profit < 0:
        profit_status = "LOSS"
    else:
        profit_status = "BREAK_EVEN"

    # Category detailed summary with percentages
    categories_detailed = []
    for cat_name, amt in category_totals.items():
        pct = round((amt / total_expenditure * 100), 2) if total_expenditure > 0 else 0.0
        categories_detailed.append(CategorySummary(
            category=cat_name,
            amount=round(amt, 2),
            percentage=pct
        ))

    # Resolve vehicle and firm labels
    vehicle_number = None
    if vehicle_id:
        v = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if v: vehicle_number = v.vehicle_number

    firm_name = None
    if firm_id:
        f = db.query(Firm).filter(Firm.id == firm_id).first()
        if f: firm_name = f.name

    return ProfitLossResponse(
        date_from=date_from,
        date_to=date_to,
        vehicle_id=vehicle_id,
        vehicle_number=vehicle_number,
        firm_id=firm_id,
        firm_name=firm_name,
        total_income=total_income,
        total_expenditure=total_expenditure,
        net_profit=net_profit,
        profit_margin_pct=profit_margin,
        profit_margin_percent=profit_margin,
        profit_status=profit_status,
        total_trips=total_trips,
        total_rtkm=total_rtkm,
        category_breakdown={k: round(v, 2) for k, v in category_totals.items()},
        categories_detailed=categories_detailed
    )

def get_log_book(
    db: Session,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    vehicle_id: Optional[int] = None,
    firm_id: Optional[int] = None
) -> LogBookResponse:
    summary = get_profit_loss_summary(db, date_from, date_to, vehicle_id, firm_id)

    # 1. Fetch Trips (Incomes)
    trip_query = db.query(TankerDailyReport)
    if date_from:
        trip_query = trip_query.filter(TankerDailyReport.report_date >= date_from)
    if date_to:
        trip_query = trip_query.filter(TankerDailyReport.report_date <= date_to)
    if vehicle_id:
        trip_query = trip_query.filter(TankerDailyReport.vehicle_id == vehicle_id)
    if firm_id:
        trip_query = trip_query.join(Vehicle, TankerDailyReport.vehicle_id == Vehicle.id).filter(Vehicle.firm_id == firm_id)

    trips = trip_query.order_by(TankerDailyReport.report_date.desc()).all()

    # 2. Fetch Expenses (Expenditures)
    exp_query = db.query(VehicleExpense)
    if date_from:
        exp_query = exp_query.filter(VehicleExpense.expense_date >= date_from)
    if date_to:
        exp_query = exp_query.filter(VehicleExpense.expense_date <= date_to)
    if vehicle_id:
        exp_query = exp_query.filter(VehicleExpense.vehicle_id == vehicle_id)
    if firm_id:
        exp_query = exp_query.join(Vehicle, VehicleExpense.vehicle_id == Vehicle.id).filter(Vehicle.firm_id == firm_id)

    expenses = exp_query.order_by(VehicleExpense.expense_date.desc()).all()

    # Combine into unified chronological ledger
    entries: List[LogBookEntry] = []

    for t in trips:
        veh_num = t.vehicle.vehicle_number if t.vehicle else f"Vehicle #{t.vehicle_id}"
        firm_str = t.vehicle.firm.name if (t.vehicle and t.vehicle.firm) else None
        entries.append(LogBookEntry(
            id=f"TRIP-{t.id}",
            entry_date=t.report_date,
            vehicle_id=t.vehicle_id,
            vehicle_number=veh_num,
            firm_name=firm_str,
            entry_type="INCOME",
            category="Freight",
            description=f"Trip: {t.ul_point} (RTKM: {t.rtkm}, Rate: ₹{t.rate})",
            amount=round(t.freight, 2),
            reference_id=t.id
        ))

    for e in expenses:
        veh_num = e.vehicle.vehicle_number if e.vehicle else f"Vehicle #{e.vehicle_id}"
        firm_str = e.vehicle.firm.name if (e.vehicle and e.vehicle.firm) else None
        cat_str = e.category.value if hasattr(e.category, "value") else str(e.category)
        entries.append(LogBookEntry(
            id=f"EXP-{e.id}",
            entry_date=e.expense_date,
            vehicle_id=e.vehicle_id,
            vehicle_number=veh_num,
            firm_name=firm_str,
            entry_type="EXPENDITURE",
            category=cat_str,
            description=e.description or f"{cat_str.capitalize()} expense",
            amount=round(e.amount, 2),
            reference_id=e.id
        ))

    # Sort descending by date
    entries.sort(key=lambda x: (x.entry_date, x.entry_type == "INCOME"), reverse=True)

    return LogBookResponse(
        summary=summary,
        entries=entries
    )
