import pytest
from datetime import date

def test_admin_dashboard_envelope(client, admin_headers):
    """Verify GET /api/v1/admin/dashboard returns the exact frontend designer envelope."""
    res = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert res.status_code == 200
    
    body = res.json()
    assert body["success"] is True
    assert body["statusCode"] == 200
    assert body["code"] == "DASHBOARD_SUMMARY_FETCHED"
    assert body["message"] == "Dashboard summary retrieved successfully."
    assert isinstance(body["data"], dict)
    assert "total_vehicles" in body["data"]
    assert "active_vehicles" in body["data"]
    assert "total_freight_this_month" in body["data"]

def test_auth_login_envelope(client, test_master):
    """Verify POST /api/v1/auth/login envelope."""
    res = client.post("/api/v1/auth/login", json={
        "email": test_master.email,
        "password": "MasterPass123"
    })
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["statusCode"] == 200
    assert body["code"] == "LOGIN_SUCCESS"
    assert body["message"] == "Signed in successfully."
    assert "access_token" in body["data"]
    assert "token_type" in body["data"]

def test_vehicles_list_envelope(client, admin_headers):
    """Verify GET /api/v1/vehicles returns array wrapped in data."""
    res = client.get("/api/v1/vehicles", headers=admin_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["statusCode"] == 200
    assert body["code"] == "VEHICLES_FETCHED"
    assert body["message"] == "Vehicles retrieved successfully."
    assert isinstance(body["data"], list)

def test_vehicle_create_and_delete_envelope(client, master_headers):
    """Verify 201 Created and 200 Deleted envelopes."""
    # 1. Create Firm
    f_res = client.post("/api/v1/firms", headers=master_headers, json={"name": "Envelope Test Firm"})
    assert f_res.json()["success"] is True
    assert f_res.json()["code"] == "FIRM_CREATED"
    firm_id = f_res.json()["data"]["id"]

    # 2. Create Vehicle
    v_res = client.post("/api/v1/vehicles", headers=master_headers, json={
        "vehicle_number": "ENV01AA9999",
        "vehicle_class": "Tanker",
        "firm_id": firm_id
    })
    assert v_res.status_code == 201
    v_body = v_res.json()
    assert v_body["success"] is True
    assert v_body["statusCode"] == 201
    assert v_body["code"] == "VEHICLE_CREATED"
    assert v_body["message"] == "Vehicle registered successfully."
    vehicle_id = v_body["data"]["id"]

    # 3. Delete Vehicle
    del_res = client.delete(f"/api/v1/vehicles/{vehicle_id}", headers=master_headers)
    assert del_res.status_code in (200, 204)
    if del_res.status_code == 200:
        del_body = del_res.json()
        assert del_body["success"] is True
        assert del_body["statusCode"] == 200
        assert del_body["code"] == "VEHICLE_DELETED"
        assert del_body["message"] == "Vehicle deleted successfully."
        assert del_body["data"] is None

def test_error_envelope_403(client, admin_headers):
    """Verify 403 Forbidden error response envelope."""
    # Admin attempting to create a vehicle (Master only)
    res = client.post("/api/v1/vehicles", headers=admin_headers, json={
        "vehicle_number": "FORBIDDEN01",
        "vehicle_class": "Tanker"
    })
    assert res.status_code == 403
    body = res.json()
    assert body["success"] is False
    assert body["statusCode"] == 403
    assert body["code"] == "FORBIDDEN"
    assert "Master role required" in body["message"]
    assert body["data"] is None

def test_error_envelope_422(client, master_headers):
    """Verify 422 Validation error response envelope."""
    res = client.post("/api/v1/vehicles", headers=master_headers, json={
        # Missing required vehicle_number and vehicle_class
    })
    assert res.status_code == 422
    body = res.json()
    assert body["success"] is False
    assert body["statusCode"] == 422
    assert body["code"] == "VALIDATION_ERROR"
    assert "body" in body["message"]
    assert body["data"] is None

def test_file_export_not_wrapped(client, admin_headers):
    """Verify Excel stream export remains raw binary and is not wrapped in JSON."""
    res = client.get("/api/v1/admin/taxes/export", headers=admin_headers)
    assert res.status_code == 200
    assert "openxmlformats" in res.headers.get("content-type", "")
    assert len(res.content) > 100
