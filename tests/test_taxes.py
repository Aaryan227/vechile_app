import io
from datetime import date, timedelta
import pytest
from app.db.models.vehicle import Vehicle
from app.db.models.audit_log import AuditLog
from app.db.models.tax import TaxStatus, TaxType, ChargeType, ChallanStatus
from app.services.tax_service import compute_tax_status

@pytest.fixture
def sample_vehicle(db):
    vehicle = Vehicle(
        vehicle_number="KA01MJ9999",
        vehicle_class="Tanker",
        make="BharatBenz",
        model="2823C",
        status="ACTIVE"
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


def test_tax_status_computation():
    today = date.today()

    # 1. Unpaid, due in future -> PENDING
    status_pending = compute_tax_status(due_date=today + timedelta(days=10), valid_until=today + timedelta(days=90), payment_date=None)
    assert status_pending == TaxStatus.PENDING

    # 2. Unpaid, due date in past -> OVERDUE
    status_overdue = compute_tax_status(due_date=today - timedelta(days=5), valid_until=today + timedelta(days=90), payment_date=None)
    assert status_overdue == TaxStatus.OVERDUE

    # 3. Paid, valid until in past -> EXPIRED
    status_expired = compute_tax_status(due_date=today - timedelta(days=40), valid_until=today - timedelta(days=2), payment_date=today - timedelta(days=45))
    assert status_expired == TaxStatus.EXPIRED

    # 4. Paid, valid until within 30 days -> DUE_SOON
    status_due_soon = compute_tax_status(due_date=today - timedelta(days=100), valid_until=today + timedelta(days=15), payment_date=today - timedelta(days=100))
    assert status_due_soon == TaxStatus.DUE_SOON

    # 5. Paid, valid until > 30 days -> ACTIVE
    status_active = compute_tax_status(due_date=today - timedelta(days=100), valid_until=today + timedelta(days=180), payment_date=today - timedelta(days=100))
    assert status_active == TaxStatus.ACTIVE


def test_tax_crud_master(client, master_headers, admin_headers, sample_vehicle, db):
    today = date.today()
    payload = {
        "tax_type": "ROAD_TAX",
        "state": "Punjab",
        "tax_authority": "RTO Ludhiana",
        "amount": 42500.0,
        "period_start": str(today - timedelta(days=30)),
        "period_end": str(today + timedelta(days=335)),
        "payment_date": str(today - timedelta(days=30)),
        "due_date": str(today - timedelta(days=25)),
        "valid_from": str(today - timedelta(days=30)),
        "valid_until": str(today + timedelta(days=335)),
        "payment_reference": "TAX-REF-10029",
        "challan_number": "CH-2026-99"
    }

    # Create Tax Record
    res = client.post(f"/api/v1/vehicles/{sample_vehicle.id}/taxes", json=payload, headers=master_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["amount"] == 42500.0
    assert data["state"] == "Punjab"
    assert data["status"] == "ACTIVE"
    tax_id = data["id"]

    # Verify Audit Log
    audit = db.query(AuditLog).filter(AuditLog.action == "CREATE_TAX", AuditLog.entity_id == tax_id).first()
    assert audit is not None

    # Get Tax Record
    res_get = client.get(f"/api/v1/vehicles/{sample_vehicle.id}/taxes/{tax_id}", headers=master_headers)
    assert res_get.status_code == 200
    assert res_get.json()["id"] == tax_id

    # List Taxes for Vehicle
    res_list = client.get(f"/api/v1/vehicles/{sample_vehicle.id}/taxes", headers=master_headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1

    # Update Tax Record
    res_patch = client.patch(f"/api/v1/vehicles/{sample_vehicle.id}/taxes/{tax_id}", json={"amount": 45000.0}, headers=master_headers)
    assert res_patch.status_code == 200
    assert res_patch.json()["amount"] == 45000.0

    # Master attempting to delete tax record -> 403 Forbidden (requires Admin permission)
    res_del_master = client.delete(f"/api/v1/vehicles/{sample_vehicle.id}/taxes/{tax_id}", headers=master_headers)
    assert res_del_master.status_code == 403

    # Admin deletes tax record with required permission -> 204 No Content
    res_del_admin = client.delete(f"/api/v1/vehicles/{sample_vehicle.id}/taxes/{tax_id}", headers=admin_headers)
    assert res_del_admin.status_code == 204


def test_duplicate_tax_prevention(client, master_headers, sample_vehicle):
    today = date.today()
    payload = {
        "tax_type": "MOTOR_VEHICLE_TAX",
        "state": "Maharashtra",
        "amount": 25000.0,
        "period_start": str(today),
        "period_end": str(today + timedelta(days=365)),
        "valid_until": str(today + timedelta(days=365))
    }

    res1 = client.post(f"/api/v1/vehicles/{sample_vehicle.id}/taxes", json=payload, headers=master_headers)
    assert res1.status_code == 201

    # Duplicate creation should fail
    res2 = client.post(f"/api/v1/vehicles/{sample_vehicle.id}/taxes", json=payload, headers=master_headers)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_admin_tax_monitoring_and_restrictions(client, master_headers, admin_headers, sample_vehicle):
    today = date.today()
    payload = {
        "tax_type": "ROAD_TAX",
        "state": "Punjab",
        "amount": 10000.0,
        "period_start": str(today),
        "period_end": str(today + timedelta(days=365)),
        "valid_until": str(today + timedelta(days=365))
    }

    # Master creates tax
    res_create = client.post(f"/api/v1/vehicles/{sample_vehicle.id}/taxes", json=payload, headers=master_headers)
    assert res_create.status_code == 201

    # Admin CAN monitor/view taxes
    res_admin_get = client.get(f"/api/v1/vehicles/{sample_vehicle.id}/taxes", headers=admin_headers)
    assert res_admin_get.status_code == 200
    assert len(res_admin_get.json()) >= 1

    # Admin CANNOT create tax -> 403
    res_admin_post = client.post(f"/api/v1/vehicles/{sample_vehicle.id}/taxes", json=payload, headers=admin_headers)
    assert res_admin_post.status_code == 403


def test_government_charges_crud(client, master_headers, sample_vehicle):
    today = date.today()
    payload = {
        "charge_type": "NATIONAL_PERMIT_FEE",
        "state": "All India",
        "authority": "MoRTH",
        "amount": 16500.0,
        "period_start": str(today),
        "period_end": str(today + timedelta(days=365)),
        "payment_date": str(today),
        "valid_until": str(today + timedelta(days=365)),
        "payment_reference": "NP-REF-8899"
    }

    # Create Government Charge
    res = client.post(f"/api/v1/vehicles/{sample_vehicle.id}/government-charges", json=payload, headers=master_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["charge_type"] == "NATIONAL_PERMIT_FEE"
    charge_id = data["id"]

    # List Government Charges
    res_list = client.get(f"/api/v1/vehicles/{sample_vehicle.id}/government-charges", headers=master_headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1

    # Delete Government Charge
    res_del = client.delete(f"/api/v1/vehicles/{sample_vehicle.id}/government-charges/{charge_id}", headers=master_headers)
    assert res_del.status_code == 204


def test_challans_crud(client, master_headers, sample_vehicle):
    today = date.today()
    payload = {
        "challan_number": "CH-PUN-00123",
        "authority": "Traffic Police Amritsar",
        "reason": "Speed limit violation",
        "issue_date": str(today),
        "amount": 2000.0,
        "due_date": str(today + timedelta(days=15)),
        "status": "UNPAID"
    }

    # Create Challan
    res = client.post(f"/api/v1/vehicles/{sample_vehicle.id}/challans", json=payload, headers=master_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["challan_number"] == "CH-PUN-00123"
    challan_id = data["id"]

    # Update Challan Status to PAID
    res_patch = client.patch(f"/api/v1/vehicles/{sample_vehicle.id}/challans/{challan_id}", json={"status": "PAID", "payment_date": str(today)}, headers=master_headers)
    assert res_patch.status_code == 200
    assert res_patch.json()["status"] == "PAID"

    # List Challans
    res_list = client.get(f"/api/v1/vehicles/{sample_vehicle.id}/challans", headers=master_headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1


def test_fastag_crud(client, master_headers, admin_headers, sample_vehicle):
    # Initial fetch auto-creates record (Master or Admin monitor)
    res_get = client.get(f"/api/v1/vehicles/{sample_vehicle.id}/fastag", headers=admin_headers)
    assert res_get.status_code == 200
    assert res_get.json()["vehicle_id"] == sample_vehicle.id

    # Update FASTag info (Master only)
    payload = {
        "tag_number": "34161FFA0192837",
        "tag_provider": "ICICI Bank",
        "tag_status": "ACTIVE",
        "linked_account_ref": "ACC-998811",
        "last_balance": 3450.50,
        "notes": "Commercial fleet FASTag"
    }
    res_put = client.put(f"/api/v1/vehicles/{sample_vehicle.id}/fastag", json=payload, headers=master_headers)
    assert res_put.status_code == 200
    data = res_put.json()
    assert data["tag_number"] == "34161FFA0192837"
    assert data["last_balance"] == 3450.50


def test_fleet_queries_and_export(client, master_headers, admin_headers, sample_vehicle):
    today = date.today()
    client.post(f"/api/v1/vehicles/{sample_vehicle.id}/taxes", json={
        "tax_type": "ROAD_TAX",
        "state": "Punjab",
        "amount": 30000.0,
        "period_start": str(today),
        "period_end": str(today + timedelta(days=365)),
        "payment_date": str(today),
        "valid_until": str(today + timedelta(days=365))
    }, headers=master_headers)

    # Fleet taxes (Admin monitors)
    res_fleet = client.get("/api/v1/admin/taxes", headers=admin_headers)
    assert res_fleet.status_code == 200
    assert len(res_fleet.json()) >= 1

    # Excel export (Admin monitors)
    res_export = client.get("/api/v1/admin/taxes/export", headers=admin_headers)
    assert res_export.status_code == 200
    assert res_export.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert len(res_export.content) > 0


def test_dashboard_metrics_includes_tax_and_pending_reuploads(client, admin_headers):
    res = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "active_taxes" in data
    assert "taxes_due_soon" in data
    assert "taxes_overdue" in data
    assert "taxes_expired" in data
    assert "pending_reupload_requests" in data


def test_danda_tax_lifecycle(client, master_headers, admin_headers, sample_vehicle):
    today = date.today()
    payload = {
        "tax_type": "DANDA_TAX",
        "state": "Haryana",
        "tax_authority": "RTO Gurugram",
        "amount": 18500.0,
        "period_start": str(today - timedelta(days=10)),
        "period_end": str(today + timedelta(days=355)),
        "payment_date": str(today - timedelta(days=10)),
        "due_date": str(today - timedelta(days=5)),
        "valid_from": str(today - timedelta(days=10)),
        "valid_until": str(today + timedelta(days=355)),
        "payment_reference": "DANDA-TXN-2026-01",
        "challan_number": "DANDA-CH-9912",
        "notes": "Annual Danda Tax assessed as per Haryana Commercial Vehicles Act"
    }

    # 1. Master creates Danda Tax
    res_create = client.post(f"/api/v1/vehicles/{sample_vehicle.id}/taxes", json=payload, headers=master_headers)
    assert res_create.status_code == 201
    tax_data = res_create.json()
    assert tax_data["tax_type"] == "DANDA_TAX"
    assert tax_data["amount"] == 18500.0
    assert tax_data["state"] == "Haryana"
    assert tax_data["tax_authority"] == "RTO Gurugram"
    assert tax_data["status"] == "ACTIVE"
    tax_id = tax_data["id"]

    # 2. Master uploads receipt
    dummy_pdf = io.BytesIO(b"%PDF-1.4 dummy danda tax receipt")
    dummy_pdf.name = "danda_receipt.pdf"
    res_upload = client.post(
        f"/api/v1/vehicles/{sample_vehicle.id}/taxes/{tax_id}/receipt",
        files={"file": ("danda_receipt.pdf", dummy_pdf, "application/pdf")},
        headers=master_headers
    )
    assert res_upload.status_code == 200
    assert res_upload.json()["receipt_file_url"] is not None

    # 3. Master updates notes and amount
    res_patch = client.patch(
        f"/api/v1/vehicles/{sample_vehicle.id}/taxes/{tax_id}",
        json={"amount": 19000.0, "notes": "Updated Danda Tax assessment"},
        headers=master_headers
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["amount"] == 19000.0

    # 4. Admin monitors and retrieves Danda Tax record
    res_admin_view = client.get(f"/api/v1/vehicles/{sample_vehicle.id}/taxes/{tax_id}", headers=admin_headers)
    assert res_admin_view.status_code == 200
    assert res_admin_view.json()["tax_type"] == "DANDA_TAX"

    # 5. Master attempts to delete -> 403 (permission from admin required)
    res_master_delete = client.delete(f"/api/v1/vehicles/{sample_vehicle.id}/taxes/{tax_id}", headers=master_headers)
    assert res_master_delete.status_code == 403

    # 6. Admin deletes Danda Tax record -> 204
    res_admin_delete = client.delete(f"/api/v1/vehicles/{sample_vehicle.id}/taxes/{tax_id}", headers=admin_headers)
    assert res_admin_delete.status_code == 204


def test_green_tax_lifecycle(client, master_headers, admin_headers, sample_vehicle):
    today = date.today()
    payload = {
        "tax_type": "GREEN_TAX",
        "state": "Delhi",
        "tax_authority": "Transport Department GNCTD",
        "amount": 7500.0,
        "period_start": str(today),
        "period_end": str(today + timedelta(days=365)),
        "payment_date": str(today),
        "due_date": str(today + timedelta(days=30)),
        "valid_from": str(today),
        "valid_until": str(today + timedelta(days=365)),
        "payment_reference": "GREEN-TAX-DL-8877",
        "challan_number": "GT-DL-2026",
        "notes": "Green Tax / Environmental Cess for commercial vehicle entry"
    }

    # 1. Master creates Green Tax
    res_create = client.post(f"/api/v1/vehicles/{sample_vehicle.id}/taxes", json=payload, headers=master_headers)
    assert res_create.status_code == 201
    tax_data = res_create.json()
    assert tax_data["tax_type"] == "GREEN_TAX"
    assert tax_data["amount"] == 7500.0
    assert tax_data["state"] == "Delhi"
    assert tax_data["status"] == "ACTIVE"
    tax_id = tax_data["id"]

    # 2. Admin monitors fleet taxes and filters by tax_type GREEN_TAX
    res_fleet = client.get("/api/v1/admin/taxes?tax_type=GREEN_TAX", headers=admin_headers)
    assert res_fleet.status_code == 200
    assert any(t["id"] == tax_id for t in res_fleet.json())

    # 3. Master attempts to delete -> 403 (permission from admin required)
    res_master_delete = client.delete(f"/api/v1/vehicles/{sample_vehicle.id}/taxes/{tax_id}", headers=master_headers)
    assert res_master_delete.status_code == 403

    # 4. Admin deletes Green Tax record -> 204
    res_admin_delete = client.delete(f"/api/v1/vehicles/{sample_vehicle.id}/taxes/{tax_id}", headers=admin_headers)
    assert res_admin_delete.status_code == 204
