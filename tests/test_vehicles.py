def test_create_vehicle_master(client, master_headers):
    # Create a firm first
    f_res = client.post("/api/v1/firms", headers=master_headers, json={"name": "Fleet Master Firm 1"})
    firm_id = f_res.json()["id"]

    response = client.post("/api/v1/vehicles", headers=master_headers, json={
        "vehicle_number": "KA01XY9999",
        "vehicle_class": "Tanker",
        "firm_id": firm_id,
        "make": "Ashok Leyland",
        "model": "3520",
        "chassis_number": "CHASSIS9999",
        "engine_number": "ENGINE9999"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["vehicle_number"] == "KA01XY9999"
    assert data["firm_name"] == "Fleet Master Firm 1"

def test_admin_cannot_create_vehicle(client, master_headers, admin_headers):
    f_res = client.post("/api/v1/firms", headers=master_headers, json={"name": "Fleet Master Firm 2"})
    firm_id = f_res.json()["id"]

    response = client.post("/api/v1/vehicles", headers=admin_headers, json={
        "vehicle_number": "KA01XY8888",
        "vehicle_class": "Tanker",
        "firm_id": firm_id
    })
    assert response.status_code == 403
    assert "Master role required" in response.json()["detail"]

def test_admin_can_view_vehicles_monitoring(client, master_headers, admin_headers):
    # Master creates firm & vehicle
    f_res = client.post("/api/v1/firms", headers=master_headers, json={"name": "Fleet Master Firm 3"})
    firm_id = f_res.json()["id"]

    v_res = client.post("/api/v1/vehicles", headers=master_headers, json={
        "vehicle_number": "MH14ZZ1111",
        "vehicle_class": "Tanker",
        "firm_id": firm_id
    })
    assert v_res.status_code == 201
    vehicle_id = v_res.json()["id"]

    # Admin monitors list and single vehicle
    list_res = client.get("/api/v1/vehicles", headers=admin_headers)
    assert list_res.status_code == 200
    assert any(v["id"] == vehicle_id for v in list_res.json())

    get_res = client.get(f"/api/v1/vehicles/{vehicle_id}", headers=admin_headers)
    assert get_res.status_code == 200
    assert get_res.json()["vehicle_number"] == "MH14ZZ1111"

def test_master_update_and_delete_vehicle(client, master_headers):
    f_res = client.post("/api/v1/firms", headers=master_headers, json={"name": "Fleet Master Firm 4"})
    firm_id = f_res.json()["id"]

    v_res = client.post("/api/v1/vehicles", headers=master_headers, json={
        "vehicle_number": "DL01AA1234",
        "vehicle_class": "Tanker",
        "firm_id": firm_id
    })
    assert v_res.status_code == 201
    vehicle_id = v_res.json()["id"]

    update_res = client.patch(f"/api/v1/vehicles/{vehicle_id}", headers=master_headers, json={
        "status": "MAINTENANCE"
    })
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "MAINTENANCE"

    del_res = client.delete(f"/api/v1/vehicles/{vehicle_id}", headers=master_headers)
    assert del_res.status_code in (200, 204)
    if del_res.status_code == 200:
        assert del_res.json()["success"] is True
