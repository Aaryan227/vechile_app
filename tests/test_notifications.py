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


def test_tax_overdue_on_update_triggers_push_notification(client, master_headers, admin_headers):
    # 1. Register admin device token
    client.post("/api/v1/users/device-token", headers=admin_headers, json={
        "device_token": "admin_fcm_token_tax_update_test",
        "platform": "android"
    })

    # 2. Create vehicle and active tax record
    firm_res = client.post("/api/v1/firms", headers=master_headers, json={"name": "Tax Update Firm"})
    firm_id = firm_res.json()["id"]

    v_res = client.post("/api/v1/vehicles", headers=master_headers, json={
        "vehicle_number": "DL01TX1111",
        "vehicle_class": "Tanker",
        "firm_id": firm_id
    })
    vehicle_id = v_res.json()["id"]

    # Tax valid in the future, due date in future
    tax_res = client.post(f"/api/v1/vehicles/{vehicle_id}/taxes", headers=master_headers, json={
        "tax_type": "ROAD_TAX",
        "state": "DL",
        "period_start": "2026-01-01",
        "period_end": "2026-12-31",
        "amount": 5000.0,
        "due_date": "2026-12-01",
        "valid_until": "2026-12-31"
    })
    assert tax_res.status_code == 201
    tax_id = tax_res.json()["id"]

    # 3. Update tax record with past due date and no payment date -> marks status OVERDUE
    with patch("firebase_admin.messaging.send_each_for_multicast") as mock_send, \
         patch("app.services.notification_service.init_firebase", return_value=True):

        mock_response = MagicMock()
        mock_response.success_count = 1
        mock_response.responses = [MagicMock(success=True)]
        mock_send.return_value = mock_response

        patch_res = client.patch(f"/api/v1/vehicles/{vehicle_id}/taxes/{tax_id}", headers=master_headers, json={
            "due_date": "2026-09-01"  # Past due date -> triggers OVERDUE
        })
        assert patch_res.status_code == 200
        assert patch_res.json()["status"] == "OVERDUE"

        assert mock_send.called
        sent_message = mock_send.call_args[0][0]
        assert "admin_fcm_token_tax_update_test" in sent_message.tokens
        assert "Tax Payment Overdue" in sent_message.notification.title
        assert "DL01TX1111" in sent_message.notification.body


def test_admin_check_expiring_documents_endpoint(client, master_headers, admin_headers):
    from datetime import date, timedelta
    from io import BytesIO

    with patch("firebase_admin.messaging.send_each_for_multicast") as mock_send, \
         patch("app.services.notification_service.init_firebase", return_value=True):

        mock_response = MagicMock()
        mock_response.success_count = 1
        mock_response.responses = [MagicMock(success=True)]
        mock_send.return_value = mock_response

        # 1. Register admin device token
        client.post("/api/v1/users/device-token", headers=admin_headers, json={
            "device_token": "admin_fcm_token_expiring_docs_endpoint",
            "platform": "android"
        })

        # 2. Create vehicle, upload document expiring in 4 days, and create an overdue tax record
        firm_res = client.post("/api/v1/firms", headers=master_headers, json={"name": "Expiring Docs Test Firm"})
        firm_id = firm_res.json()["id"]

        v_res = client.post("/api/v1/vehicles", headers=master_headers, json={
            "vehicle_number": "RJ14EX7777",
            "vehicle_class": "Tanker",
            "firm_id": firm_id
        })
        vehicle_id = v_res.json()["id"]

        exp_date_str = (date.today() + timedelta(days=4)).isoformat()
        client.post("/api/v1/documents/upload", headers=master_headers, data={
            "vehicle_id": vehicle_id,
            "document_type": "FITNESS",
            "document_number": "FIT7777",
            "expiry_date": exp_date_str
        }, files={"file": ("fitness.pdf", BytesIO(b"%PDF-1.4 test fitness cert"), "application/pdf")})

        # Create an overdue tax record
        client.post(f"/api/v1/vehicles/{vehicle_id}/taxes", headers=master_headers, json={
            "tax_type": "STATE_VEHICLE_TAX",
            "state": "RJ",
            "period_start": "2026-01-01",
            "period_end": "2026-06-30",
            "amount": 4200.0,
            "due_date": "2026-06-01", # Past due date
            "valid_until": "2026-06-30"
        })

        # Reset mock calls after setup
        mock_send.reset_mock()

        # 3. Call POST /api/v1/admin/notifications/compliance-scan
        scan_res = client.post("/api/v1/admin/notifications/compliance-scan?days=7", headers=admin_headers)
        assert scan_res.status_code == 200
        data = scan_res.json()
        assert data["notifications_sent"] >= 2
        assert data["expiring_documents_notified"] >= 1
        assert data["overdue_taxes_notified"] >= 1
        assert data["days_threshold"] == 7

        assert mock_send.called
        # Check titles sent
        titles = [call[0][0].notification.title for call in mock_send.call_args_list]
        assert any("Document Expiring Soon" in t for t in titles)
        assert any("Tax Payment Overdue" in t for t in titles)

