from io import BytesIO
from app.db.models.vehicle import Vehicle
from app.db.models.vehicle_assignment import VehicleAssignment

def test_document_upload_and_reupload_permission_flow(client, db, test_admin, test_driver, admin_headers, driver_headers):
    # 1. Admin creates a vehicle
    v = Vehicle(
        vehicle_number="KA01AB1234",
        vehicle_class="Tanker",
        chassis_number="CHASSIS12345",
        engine_number="ENGINE12345"
    )
    db.add(v)
    db.commit()
    db.refresh(v)

    # 2. Admin assigns vehicle to driver
    assignment = VehicleAssignment(vehicle_id=v.id, driver_id=test_driver.id, is_active=True)
    db.add(assignment)
    db.commit()

    # 3. Driver uploads RC document for the 1st time (Allowed)
    file_content = b"fake pdf content"
    res1 = client.post(
        "/api/v1/documents/upload",
        headers=driver_headers,
        data={
            "vehicle_id": v.id,
            "document_type": "RC",
            "expiry_date": "2028-12-31",
            "document_number": "RC123456"
        },
        files={"file": ("rc.pdf", BytesIO(file_content), "application/pdf")}
    )
    assert res1.status_code == 201
    doc_id = res1.json()["id"]
    assert res1.json()["can_reupload"] is False

    # 4. Driver attempts to upload RC document again without permission (Forbidden)
    res2 = client.post(
        "/api/v1/documents/upload",
        headers=driver_headers,
        data={
            "vehicle_id": v.id,
            "document_type": "RC",
            "expiry_date": "2029-12-31",
            "document_number": "RC123456-UPDATED"
        },
        files={"file": ("rc2.pdf", BytesIO(file_content), "application/pdf")}
    )
    assert res2.status_code == 403
    assert "permission from an admin" in res2.json()["detail"]

    # 5. Admin grants reupload permission
    res3 = client.post(
        f"/api/v1/documents/{doc_id}/allow-reupload",
        headers=admin_headers
    )
    assert res3.status_code == 200
    assert res3.json()["can_reupload"] is True

    # 6. Driver reuploads RC document after admin granted permission (Allowed)
    res4 = client.post(
        "/api/v1/documents/upload",
        headers=driver_headers,
        data={
            "vehicle_id": v.id,
            "document_type": "RC",
            "expiry_date": "2030-12-31",
            "document_number": "RC123456-NEW"
        },
        files={"file": ("rc3.pdf", BytesIO(file_content), "application/pdf")}
    )
    assert res4.status_code == 201
    assert res4.json()["can_reupload"] is False

def test_change_password_endpoint_removed(client, driver_headers):
    res = client.post(
        "/api/v1/auth/change-password",
        headers=driver_headers,
        json={"old_password": "DriverPass123", "new_password": "NewDriverPass123!"}
    )
    assert res.status_code == 404
