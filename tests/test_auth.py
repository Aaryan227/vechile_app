def test_master_registration_success(client):
    response = client.post("/api/v1/auth/register", json={
        "name": "New Master",
        "email": "newmaster@vahaansetu.com",
        "phone": "9887766551",
        "password": "Password123",
        "role": "master",
        "access_code": "MASTER_ACCESS_2026"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newmaster@vahaansetu.com"
    assert data["role"] == "master"

def test_master_registration_invalid_code(client):
    response = client.post("/api/v1/auth/register", json={
        "name": "Failed Master",
        "email": "failedmaster@vahaansetu.com",
        "password": "Password123",
        "role": "master",
        "access_code": "WRONG_SECRET"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid Master Access Code"

def test_admin_registration_success(client):
    response = client.post("/api/v1/auth/register", json={
        "name": "New Admin",
        "email": "newadmin@vahaansetu.com",
        "phone": "9887766552",
        "password": "Password123",
        "role": "admin",
        "access_code": "ADMIN_ACCESS_2026"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newadmin@vahaansetu.com"
    assert data["role"] == "admin"

def test_admin_registration_invalid_code(client):
    response = client.post("/api/v1/auth/register", json={
        "name": "Failed Admin",
        "email": "failedadmin@vahaansetu.com",
        "password": "Password123",
        "role": "admin",
        "access_code": "WRONG_SECRET"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid Admin Access Code"

def test_driver_registration_rejected(client):
    response = client.post("/api/v1/auth/register", json={
        "name": "Driver Attempt",
        "email": "driverattempt@vahaansetu.com",
        "password": "Password123",
        "role": "driver"
    })
    assert response.status_code == 400
    assert "no longer supported" in response.json()["detail"]

def test_login_success(client, test_master):
    response = client.post("/api/v1/auth/login", json={
        "email": test_master.email,
        "password": "MasterPass123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_login_form_success(client, test_master):
    response = client.post("/api/v1/auth/login", data={
        "username": test_master.email,
        "password": "MasterPass123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_login_invalid_password(client, test_master):
    response = client.post("/api/v1/auth/login", json={
        "email": test_master.email,
        "password": "WrongPassword"
    })
    assert response.status_code == 401

def test_get_current_user_me(client, master_headers):
    response = client.get("/api/v1/auth/me", headers=master_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "master"
