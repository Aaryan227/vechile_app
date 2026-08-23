from pydantic import BaseModel

class DashboardMetricsResponse(BaseModel):
    total_vehicles: int
    active_vehicles: int
    total_drivers: int
    expired_documents: int
    documents_expiring_soon: int
    total_tanker_entries_this_month: int
    total_freight_this_month: float
