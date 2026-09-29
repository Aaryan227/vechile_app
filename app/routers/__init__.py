from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.vehicles import router as vehicles_router
from app.routers.documents import router as documents_router
from app.routers.tanker_reports import router as tanker_reports_router
from app.routers.admin import router as admin_router
from app.routers.reports import router as reports_router
from app.routers.taxes import router as taxes_router
from app.routers.firms import router as firms_router
from app.routers.route_points import router as route_points_router
from app.routers.expenses import router as expenses_router
from app.routers.financials import router as financials_router

__all__ = [
    "auth_router",
    "users_router",
    "vehicles_router",
    "documents_router",
    "tanker_reports_router",
    "admin_router",
    "reports_router",
    "taxes_router",
    "firms_router",
    "route_points_router",
    "expenses_router",
    "financials_router"
]
