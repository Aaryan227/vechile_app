from unittest.mock import patch, MagicMock
from app.db.models.user import User, UserRole

def test_register_and_unregister_device_token(client, admin_headers):
    # 1. Register device token
    token_payload = {
        "device_token": "fcm_device_test_token_abcdef123456",
        "platform": "android"
    }
    res = client.post("/api/v1/users/device-token", headers=admin_headers, json=token_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["device_token"] == token_payload["device_token"]
    assert data["platform"] == "android"

    # 2. Register again (upsert check)
    res2 = client.post("/api/v1/users/device-token", headers=admin_headers, json={
        "device_token": "fcm_device_test_token_abcdef123456",
        "platform": "ios"
    })
    assert res2.status_code == 201
    assert res2.json()["platform"] == "ios"

    # 3. Unregister device token
    del_res = client.request("DELETE", "/api/v1/users/device-token", headers=admin_headers, json=token_payload)
    assert del_res.status_code == 200


def test_document_reupload_triggers_push_notification(client, master_headers, admin_headers):
    # 1. Register an admin device token
    client.post("/api/v1/users/device-token", headers=admin_headers, json={
        "device_token": "admin_fcm_token_notify_doc_test",
        "platform": "android"
    })

    # 2. Create vehicle and upload a document
    firm_res = client.post("/api/v1/firms", headers=master_headers, json={"name": "Push Notification Logistics"})
    firm_id = firm_res.json()["id"]

    v_res = client.post("/api/v1/vehicles", headers=master_headers, json={
        "vehicle_number": "UP16PN9999",
        "vehicle_class": "Tanker",
        "firm_id": firm_id
    })
    vehicle_id = v_res.json()["id"]

    from io import BytesIO
    doc_res = client.post("/api/v1/documents/upload", headers=master_headers, data={
        "vehicle_id": vehicle_id,
        "document_type": "RC",
        "document_number": "RC9999",
        "expiry_date": "2027-01-01"
    }, files={"file": ("rc.pdf", BytesIO(b"%PDF-1.4 test fitness file"), "application/pdf")})
    assert doc_res.status_code == 201
    doc_id = doc_res.json()["id"]

    # 3. Mock Firebase messaging and request re-upload as Master
    with patch("firebase_admin.messaging.send_each_for_multicast") as mock_send, \
         patch("app.services.notification_service.init_firebase", return_value=True):
        
        mock_response = MagicMock()
        mock_response.success_count = 1
        mock_response.responses = [MagicMock(success=True)]
        mock_send.return_value = mock_response

        req_res = client.post(f"/api/v1/documents/{doc_id}/request-reupload", headers=master_headers, json={
            "reason": "Updated fitness certificate scanned incorrectly"
        })
        assert req_res.status_code == 200

        # Assert notification was triggered
        assert mock_send.called
        sent_message = mock_send.call_args[0][0]
        assert "admin_fcm_token_notify_doc_test" in sent_message.tokens
        assert "Document Re-Upload" in sent_message.notification.title
        assert "UP16PN9999" in sent_message.notification.body


def test_fastag_deficit_triggers_push_notification(client, master_headers, admin_headers):
    # 1. Register admin device token
    client.post("/api/v1/users/device-token", headers=admin_headers, json={
        "device_token": "admin_fcm_token_notify_fastag_test",
        "platform": "android"
    })

    # 2. Create vehicle and set FASTag balance
    firm_res = client.post("/api/v1/firms", headers=master_headers, json={"name": "Fastag Push Transport"})
    firm_id = firm_res.json()["id"]

    v_res = client.post("/api/v1/vehicles", headers=master_headers, json={
        "vehicle_number": "HR55FT8888",
        "vehicle_class": "Tanker",
        "firm_id": firm_id
    })
    vehicle_id = v_res.json()["id"]

    client.put(f"/api/v1/vehicles/{vehicle_id}/fastag", headers=master_headers, json={
        "tag_number": "TAG8888PUSH",
        "tag_provider": "SBI",
        "tag_status": "ACTIVE",
        "last_balance": 1000.0
    })

    # 3. Log toll expense exceeding balance: ₹1500 (Remaining = -₹500)
    with patch("firebase_admin.messaging.send_each_for_multicast") as mock_send, \
         patch("app.services.notification_service.init_firebase", return_value=True):

        mock_response = MagicMock()
        mock_response.success_count = 1
        mock_response.responses = [MagicMock(success=True)]
        mock_send.return_value = mock_response

        exp_res = client.post("/api/v1/expenses", headers=master_headers, json={
            "vehicle_id": vehicle_id,
            "expense_date": "2026-10-13",
            "category": "toll",
            "amount": 1500.0,
            "description": "Toll toll crossing"
        })
        assert exp_res.status_code == 201

        # Assert notification was triggered
        assert mock_send.called
        sent_message = mock_send.call_args[0][0]
        assert "admin_fcm_token_notify_fastag_test" in sent_message.tokens
        assert "FASTag Deficit" in sent_message.notification.title
        assert "HR55FT8888" in sent_message.notification.body
