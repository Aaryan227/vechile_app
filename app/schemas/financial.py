from datetime import date
from typing import List, Dict, Optional
from pydantic import BaseModel, ConfigDict

class CategorySummary(BaseModel):
    category: str
    amount: float
    percentage: float

class ProfitLossResponse(BaseModel):
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    vehicle_id: Optional[int] = None
    vehicle_number: Optional[str] = None
    firm_id: Optional[int] = None
    firm_name: Optional[str] = None
    total_income: float = 0.0          # Total freight earned from trips
    total_expenditure: float = 0.0     # Total of all expenses
    net_profit: float = 0.0            # Income - Expenditure
    profit_margin_pct: float = 0.0     # (Net Profit / Income) * 100
    profit_margin_percent: float = 0.0 # Frontend convenience
    profit_status: str = "PROFIT"      # PROFIT, LOSS, BREAK_EVEN
    total_trips: int = 0
    total_rtkm: float = 0.0
    category_breakdown: Dict[str, float] = {}
    categories_detailed: List[CategorySummary] = []

class LogBookEntry(BaseModel):
    id: str
    entry_date: date
    vehicle_id: int
    vehicle_number: str
    firm_name: Optional[str] = None
    entry_type: str                   # INCOME or EXPENDITURE
    category: str                     # e.g., "Freight", "tyre", "battery", "maintenance", "salary", etc.
    description: Optional[str] = None
    amount: float
    reference_id: Optional[int] = None

class LogBookResponse(BaseModel):
    summary: ProfitLossResponse
    entries: List[LogBookEntry] = []
