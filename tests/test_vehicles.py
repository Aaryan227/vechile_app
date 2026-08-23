def test_create_vehicle_admin(client, admin_headers):
    response = client.post("/api/v1/vehicles", headers=admin_headers, json={
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

def test_driver_cannot_create_vehicle(client, driver_headers):
    response = client.post("/api/v1/vehicles", headers=driver_headers, json={
        "vehicle_number": "KA01XY8888",
        "vehicle_class": "Tanker"
    })
    assert response.status_code == 403

def test_assign_driver_to_vehicle(client, admin_headers, test_driver):
    # First create vehicle
    v_res = client.post("/api/v1/vehicles", headers=admin_headers, json={
        "vehicle_number": "MH14ZZ1111",
        "vehicle_class": "Tanker"
    })
    vehicle_id = v_res.json()["id"]

    # Assign driver
    assign_res = client.post(f"/api/v1/vehicles/{vehicle_id}/assign", headers=admin_headers, json={
        "driver_id": test_driver.id
    })
    assert assign_res.status_code == 200

    # Get vehicle details
    get_res = client.get(f"/api/v1/vehicles/{vehicle_id}", headers=admin_headers)
    assert get_res.status_code == 200
    assert get_res.json()["active_driver"]["id"] == test_driver.id
