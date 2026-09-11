def test_create_vehicle_master(client, master_headers):
    response = client.post("/api/v1/vehicles", headers=master_headers, json={
        "vehicle_number": "KA01XY9999",
        "vehicle_class": "Tanker",
        "make": "Ashok Leyland",
        "model": "3520",
        "chassis_number": "CHASSIS9999",
        "engine_number": "ENGINE9999"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["vehicle_number"] == "KA01XY9999"

def test_admin_cannot_create_vehicle(client, admin_headers):
    response = client.post("/api/v1/vehicles", headers=admin_headers, json={
        "vehicle_number": "KA01XY8888",
        "vehicle_class": "Tanker"
    })
    assert response.status_code == 403
    assert "Master role required" in response.json()["detail"]

def test_admin_can_view_vehicles_monitoring(client, master_headers, admin_headers):
    # Master creates vehicle
    v_res = client.post("/api/v1/vehicles", headers=master_headers, json={
        "vehicle_number": "MH14ZZ1111",
        "vehicle_class": "Tanker"
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
    v_res = client.post("/api/v1/vehicles", headers=master_headers, json={
        "vehicle_number": "DL01AA1234",
        "vehicle_class": "Tanker"
    })
    vehicle_id = v_res.json()["id"]

    update_res = client.patch(f"/api/v1/vehicles/{vehicle_id}", headers=master_headers, json={
        "status": "MAINTENANCE"
    })
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "MAINTENANCE"

    del_res = client.delete(f"/api/v1/vehicles/{vehicle_id}", headers=master_headers)
    assert del_res.status_code == 204
