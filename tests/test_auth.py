def test_driver_registration(client):
    response = client.post("/api/v1/auth/register", json={
        "name": "New Driver",
        "email": "newdriver@kingspetroleum.com",
        "phone": "9887766554",
        "password": "Password123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newdriver@kingspetroleum.com"
    assert data["role"] == "driver"

def test_admin_registration_success(client):
    response = client.post("/api/v1/auth/register", json={
        "name": "New Admin",
        "email": "newadmin@kingspetroleum.com",
        "phone": "9887766555",
        "password": "Password123",
        "role": "admin",
        "admin_access_code": "ADMIN_SECRET_2026"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newadmin@kingspetroleum.com"
    assert data["role"] == "admin"

def test_admin_registration_invalid_code(client):
    response = client.post("/api/v1/auth/register", json={
        "name": "Failed Admin",
        "email": "failedadmin@kingspetroleum.com",
        "password": "Password123",
        "role": "admin",
        "admin_access_code": "WRONG_SECRET"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid Admin Access Code"

def test_login_success(client, test_admin):
    response = client.post("/api/v1/auth/login", json={
        "email": test_admin.email,
        "password": "AdminPass123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_login_invalid_password(client, test_admin):
    response = client.post("/api/v1/auth/login", json={
        "email": test_admin.email,
        "password": "WrongPassword"
    })
    assert response.status_code == 401

def test_get_current_user_me(client, admin_headers):
    response = client.get("/api/v1/auth/me", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "admin"
