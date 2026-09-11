from io import BytesIO
from app.db.models.vehicle import Vehicle

def test_document_upload_and_reupload_permission_flow(client, db, test_master, test_admin, master_headers, admin_headers):
    # 1. Master creates a vehicle
    v = Vehicle(
        vehicle_number="KA01AB1234",
        vehicle_class="Tanker",
        chassis_number="CHASSIS12345",
        engine_number="ENGINE12345"
    )
    db.add(v)
    db.commit()
    db.refresh(v)

    # 2. Master uploads RC document for the 1st time (Allowed)
    file_content = b"fake pdf content"
    res1 = client.post(
        "/api/v1/documents/upload",
        headers=master_headers,
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

    # 3. Master attempts to upload RC document again without permission (Forbidden)
    res2 = client.post(
        "/api/v1/documents/upload",
        headers=master_headers,
        data={
            "vehicle_id": v.id,
            "document_type": "RC",
            "expiry_date": "2029-12-31",
            "document_number": "RC123456-UPDATED"
        },
        files={"file": ("rc2.pdf", BytesIO(file_content), "application/pdf")}
    )
    assert res2.status_code == 403
    assert "approved by an Admin" in res2.json()["detail"]

    # 4. Master requests re-upload permission with a reason
    res_req = client.post(
        f"/api/v1/documents/{doc_id}/request-reupload",
        headers=master_headers,
        json={"reason": "Updated renewal policy from transport office"}
    )
    assert res_req.status_code == 200
    assert res_req.json()["reupload_requested"] is True
    assert res_req.json()["reupload_reason"] == "Updated renewal policy from transport office"

    # 5. Admin lists pending re-upload requests
    res_pending = client.get("/api/v1/documents/reupload-requests", headers=admin_headers)
    assert res_pending.status_code == 200
    pending_ids = [d["id"] for d in res_pending.json()]
    assert doc_id in pending_ids

    # 6. Admin approves re-upload permission
    res3 = client.post(
        f"/api/v1/documents/{doc_id}/allow-reupload",
        headers=admin_headers
    )
    assert res3.status_code == 200
    assert res3.json()["can_reupload"] is True
    assert res3.json()["reupload_requested"] is False

    # 7. Master re-uploads RC document after Admin granted permission (Allowed)
    res4 = client.post(
        "/api/v1/documents/upload",
        headers=master_headers,
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

    # 8. Admin cannot upload documents directly (Only Master can)
    res_admin_upload = client.post(
        "/api/v1/documents/upload",
        headers=admin_headers,
        data={
            "vehicle_id": v.id,
            "document_type": "INSURANCE",
            "expiry_date": "2029-12-31",
            "document_number": "INS-99"
        },
        files={"file": ("ins.pdf", BytesIO(file_content), "application/pdf")}
    )
    assert res_admin_upload.status_code == 403

def test_admin_reject_reupload_flow(client, db, test_master, test_admin, master_headers, admin_headers):
    v = Vehicle(
        vehicle_number="KA02CD5678",
        vehicle_class="Tanker",
        chassis_number="CHASSIS5678",
        engine_number="ENGINE5678"
    )
    db.add(v)
    db.commit()
    db.refresh(v)

    # Initial upload by Master
    res1 = client.post(
        "/api/v1/documents/upload",
        headers=master_headers,
        data={
            "vehicle_id": v.id,
            "document_type": "FITNESS",
            "expiry_date": "2027-12-31",
            "document_number": "FIT-11"
        },
        files={"file": ("fit.pdf", BytesIO(b"content"), "application/pdf")}
    )
    assert res1.status_code == 201
    doc_id = res1.json()["id"]

    # Master requests re-upload
    client.post(
        f"/api/v1/documents/{doc_id}/request-reupload",
        headers=master_headers,
        json={"reason": "Incorrect test scan"}
    )

    # Admin rejects
    res_rej = client.post(f"/api/v1/documents/{doc_id}/reject-reupload", headers=admin_headers)
    assert res_rej.status_code == 200
    assert res_rej.json()["can_reupload"] is False
    assert res_rej.json()["reupload_requested"] is False

def test_change_password_endpoint(client, master_headers):
    res = client.post(
        "/api/v1/auth/change-password",
        headers=master_headers,
        json={"old_password": "MasterPass123", "new_password": "NewMasterPass123!"}
    )
    assert res.status_code == 200
    assert res.json()["message"] == "Password changed successfully"
