def test_create_firm_by_master(client, master_headers):
    response = client.post("/api/v1/firms", headers=master_headers, json={
        "name": "Apex Logistics Firm",
        "registration_number": "GST12345678",
        "contact_person": "John Doe",
        "phone": "9876543210"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Apex Logistics Firm"
    assert "id" in data

def test_duplicate_firm_rejected(client, master_headers):
    client.post("/api/v1/firms", headers=master_headers, json={
        "name": "Unique Firm"
    })
    response = client.post("/api/v1/firms", headers=master_headers, json={
        "name": "Unique Firm"
    })
    assert response.status_code == 409

def test_add_vehicle_requires_firm(client, master_headers):
    # Try adding a vehicle without firm_id
    response = client.post("/api/v1/vehicles", headers=master_headers, json={
        "vehicle_number": "WB11AA0001",
        "vehicle_class": "Tanker"
    })
    assert response.status_code == 422  # validation error: firm_id missing

    # Now create a firm first
    f_res = client.post("/api/v1/firms", headers=master_headers, json={
        "name": "Transport Corporation"
    })
    firm_id = f_res.json()["id"]

    # Now add vehicle with compulsory firm_id
    v_res = client.post("/api/v1/vehicles", headers=master_headers, json={
        "vehicle_number": "WB11AA0001",
        "vehicle_class": "Tanker",
        "firm_id": firm_id
    })
    assert v_res.status_code == 201
    assert v_res.json()["firm_name"] == "Transport Corporation"
    assert v_res.json()["firm_id"] == firm_id
