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
    taxes_router
)
from app.db.models.user import User, UserRole
from app.db.models.vehicle import Vehicle
from app.db.models.vehicle_assignment import VehicleAssignment
from app.core.security import get_password_hash

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

        # Check if sample vehicle exists
        vehicle = db.query(Vehicle).filter(Vehicle.vehicle_number == "MH12AB1234").first()
        if not vehicle:
            vehicle = Vehicle(
                vehicle_number="MH12AB1234",
                vehicle_class="Tanker",
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
    except Exception as e:
        db.rollback()
    finally:
        db.close()

from sqlalchemy import text

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure PostgreSQL compatibility & create tables
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
