import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.db.models.user import User, UserRole

TEST_DB_URL = "sqlite:///./test_vehicle_logistics.db"

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("./test_vehicle_logistics.db"):
        try:
            os.remove("./test_vehicle_logistics.db")
        except OSError:
            pass

@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db):
    def _get_test_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def test_admin(db):
    admin = User(
        name="Test Admin",
        email="testadmin@kingspetroleum.com",
        phone="9998887770",
        password_hash=get_password_hash("AdminPass123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin

@pytest.fixture
def test_driver(db):
    driver = User(
        name="Test Driver",
        email="testdriver@kingspetroleum.com",
        phone="9998887771",
        password_hash=get_password_hash("DriverPass123"),
        role=UserRole.DRIVER,
        is_active=True
    )
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return driver

@pytest.fixture
def admin_headers(test_admin):
    token = create_access_token(subject=test_admin.id, role=test_admin.role.value)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def driver_headers(test_driver):
    token = create_access_token(subject=test_driver.id, role=test_driver.role.value)
    return {"Authorization": f"Bearer {token}"}
