import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger("uvicorn.error")

from app.core.config import settings
from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.routers import (
    auth_router,
    users_router,
    vehicles_router,
    documents_router,
    tanker_reports_router,
    admin_router,
    reports_router,
    taxes_router,
    firms_router,
    route_points_router,
    expenses_router,
    financials_router
)
from app.db.models.user import User, UserRole
from app.db.models.firm import Firm
from app.db.models.vehicle import Vehicle
from app.db.models.route_point import RoutePoint
from app.core.security import get_password_hash
from sqlalchemy import text

def seed_initial_data():
    db = SessionLocal()
    try:
        # Migrate existing admin to MASTER so previous credentials maintain full operational access
        old_admin = db.query(User).filter(User.email == "admin@kingspetroleum.com").first()
        if old_admin and old_admin.role != UserRole.MASTER:
            old_admin.role = UserRole.MASTER
            db.commit()

        # Ensure Master user exists
        master = db.query(User).filter(User.email == "master@vahaansetu.com").first()
        if not master:
            phone = "9800000001"
            if db.query(User).filter(User.phone == phone).first():
                phone = None
            master = User(
                name="Fleet Master",
                email="master@vahaansetu.com",
                phone=phone,
                password_hash=get_password_hash("Master@123456"),
                role=UserRole.MASTER,
                is_active=True
            )
            db.add(master)
            db.commit()
            db.refresh(master)

        # Ensure Admin user exists (Auditor / Re-upload Approver)
        admin = db.query(User).filter(User.email == "admin@vahaansetu.com").first()
        if not admin:
            phone = "9800000002"
            if db.query(User).filter(User.phone == phone).first():
                phone = None
            admin = User(
                name="Compliance Admin",
                email="admin@vahaansetu.com",
                phone=phone,
                password_hash=get_password_hash("Admin@123456"),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)

        # Ensure default firm exists
        default_firm = db.query(Firm).first()
        if not default_firm:
            default_firm = Firm(
                name="Kings Petroleum",
                registration_number="27ABCDE1234F1Z5",
                contact_person="Master Manager",
                phone="9800000001",
                is_active=True,
                created_by=master.id if master else None
            )
            db.add(default_firm)
            db.commit()
            db.refresh(default_firm)

        # Check if sample vehicle exists
        vehicle = db.query(Vehicle).filter(Vehicle.vehicle_number == "MH12AB1234").first()
        if not vehicle:
            vehicle = Vehicle(
                vehicle_number="MH12AB1234",
                vehicle_class="Tanker",
                firm_id=default_firm.id,
                make="Tata Motors",
                model="LPT 3518",
                manufacture_year=2022,
                chassis_number="MAT618012N12345",
                engine_number="6BT5.9L12345",
                status="ACTIVE"
            )
            db.add(vehicle)
            db.commit()
            db.refresh(vehicle)
        elif vehicle.firm_id is None:
            vehicle.firm_id = default_firm.id
            db.commit()

        # Update any vehicles without firm_id to default_firm
        try:
            db.execute(text(f"UPDATE vehicles SET firm_id = {default_firm.id} WHERE firm_id IS NULL"))
            db.commit()
        except Exception:
            pass

        # Seed sample route points if none exist
        if db.query(RoutePoint).count() == 0:
            sample_points = [
                RoutePoint(name="Pakuria KSK", point_type="UNLOADING", default_rtkm=265.6, default_rate=3.559476, pump_station="Pakuria KSK"),
                RoutePoint(name="Budge Budge Terminal", point_type="LOADING", default_rtkm=180.0, default_rate=3.559476, pump_station="Budge Budge HPCL"),
                RoutePoint(name="Haldia Depot", point_type="LOADING", default_rtkm=320.0, default_rate=3.559476, pump_station="Haldia IOCL"),
                RoutePoint(name="Mogra Tank Farm", point_type="UNLOADING", default_rtkm=145.2, default_rate=3.559476, pump_station="Mogra IOCL")
            ]
            db.add_all(sample_points)
            db.commit()

    except Exception as e:
        logger.error(f"Seed error: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure PostgreSQL & SQLite compatibility & create tables
    try:
        with engine.connect() as conn:
            if engine.dialect.name == "postgresql":
                try:
                    conn.execute(text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'MASTER'"))
                    conn.execute(text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'master'"))
                    conn.commit()
                except Exception:
                    pass
                try:
                    conn.execute(text("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(20) USING role::text"))
                    conn.commit()
                except Exception:
                    pass
                try:
                    doc_types = ["EXPLOSIVE_LICENSE", "EXPLOSIVE_VEHICLE_CERTIFICATE", "PESO_CERTIFICATE", "SAFETY_CERTIFICATE", "OTHER_CERTIFICATE", "NATIONAL_PERMIT"]
                    for dt in doc_types:
                        try:
                            conn.execute(text(f"ALTER TYPE documenttype ADD VALUE IF NOT EXISTS '{dt}'"))
                            conn.commit()
                        except Exception:
                            pass
                    conn.execute(text("ALTER TABLE documents ALTER COLUMN document_type TYPE VARCHAR(50) USING document_type::text"))
                    conn.commit()
                except Exception:
                    pass
                try:
                    tax_types = ["DANDA_TAX", "GREEN_TAX"]
                    for tt in tax_types:
                        try:
                            conn.execute(text(f"ALTER TYPE taxtype ADD VALUE IF NOT EXISTS '{tt}'"))
                            conn.commit()
                        except Exception:
                            pass
                    conn.execute(text("ALTER TABLE vehicle_tax_records ALTER COLUMN tax_type TYPE VARCHAR(50) USING tax_type::text"))
                    conn.commit()
                except Exception:
                    pass
                try:
                    conn.execute(text("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS firm_id INTEGER REFERENCES firms(id)"))
                    conn.commit()
                except Exception:
                    pass
            elif engine.dialect.name == "sqlite":
                try:
                    conn.execute(text("ALTER TABLE vehicles ADD COLUMN firm_id INTEGER REFERENCES firms(id)"))
                    conn.commit()
                except Exception:
                    pass
    except Exception as e:
        logger.warning(f"Database dialect compatibility check notice: {e}")

    Base.metadata.create_all(bind=engine)
    seed_initial_data()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler to prevent returning internal tracebacks to client while preserving HTTP exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None)
        )
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please contact system administrator."}
    )

# Include Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(vehicles_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(tanker_reports_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
app.include_router(taxes_router, prefix=settings.API_V1_STR)
app.include_router(firms_router, prefix=settings.API_V1_STR)
app.include_router(route_points_router, prefix=settings.API_V1_STR)
app.include_router(expenses_router, prefix=settings.API_V1_STR)
app.include_router(financials_router, prefix=settings.API_V1_STR)

# Serve Web Frontend static files
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": f"Welcome to {settings.APP_NAME}. Access API documentation at /docs"}
