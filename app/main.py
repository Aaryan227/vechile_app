import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

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
    reports_router
)
from app.db.models.user import User, UserRole
from app.db.models.vehicle import Vehicle
from app.db.models.vehicle_assignment import VehicleAssignment
from app.core.security import get_password_hash

def seed_initial_data():
    db = SessionLocal()
    try:
        # Check if admin user exists
        admin = db.query(User).filter(User.email == "admin@kingspetroleum.com").first()
        if not admin:
            admin = User(
                name="System Admin",
                email="admin@kingspetroleum.com",
                phone="9876543210",
                password_hash=get_password_hash("Admin@123456"),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)

        # Check if default driver exists
        driver = db.query(User).filter(User.email == "driver@kingspetroleum.com").first()
        if not driver:
            driver = User(
                name="Rahul Kumar",
                email="driver@kingspetroleum.com",
                phone="9123456789",
                password_hash=get_password_hash("Driver@123456"),
                role=UserRole.DRIVER,
                is_active=True
            )
            db.add(driver)
            db.commit()
            db.refresh(driver)

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

            # Assign driver to vehicle
            assignment = VehicleAssignment(
                vehicle_id=vehicle.id,
                driver_id=driver.id,
                is_active=True
            )
            db.add(assignment)
            db.commit()
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables & seed initial data
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

# Exception handler to prevent returning internal tracebacks to client
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
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
