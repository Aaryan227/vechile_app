import io
from datetime import date, timedelta
import pytest
from app.db.models.vehicle import Vehicle
from app.db.models.vehicle_assignment import VehicleAssignment
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


def test_tax_crud_admin(client, admin_headers, sample_vehicle, db):
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
    res = client.post(f"/api/v1/vehicles/{sample_vehicle.id}/taxes", json=payload, headers=admin_headers)
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
    res_get = client.get(f"/api/v1/vehicles/{sample_vehicle.id}/taxes/{tax_id}", headers=admin_headers)
    assert res_get.status_code == 200
    assert res_get.json()["id"] == tax_id

    # List Taxes for Vehicle
    res_list = client.get(f"/api/v1/vehicles/{sample_vehicle.id}/taxes", headers=admin_headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1

    # Update Tax Record
    res_patch = client.patch(f"/api/v1/vehicles/{sample_vehicle.id}/taxes/{tax_id}", json={"amount": 45000.0}, headers=admin_headers)
    assert res_patch.status_code == 200
    assert res_patch.json()["amount"] == 45000.0

    # Delete Tax Record
    res_del = client.delete(f"/api/v1/vehicles/{sample_vehicle.id}/taxes/{tax_id}", headers=admin_headers)
    assert res_del.status_code == 204


def test_duplicate_tax_prevention(client, admin_headers, sample_vehicle):
    today = date.today()
    payload = {
        "tax_type": "MOTOR_VEHICLE_TAX",
        "state": "Maharashtra",
        "amount": 25000.0,
        "period_start": str(today),
        "period_end": str(today + timedelta(days=365)),
        "valid_until": str(today + timedelta(days=365))
    }

    res1 = client.post(f"/api/v1/vehicles/{sample_vehicle.id}/taxes", json=payload, headers=admin_headers)
    assert res1.status_code == 201

    # Duplicate creation should fail
    res2 = client.post(f"/api/v1/vehicles/{sample_vehicle.id}/taxes", json=payload, headers=admin_headers)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_driver_access_boundaries(client, driver_headers, test_driver, sample_vehicle, db):
    today = date.today()

    # Driver not yet assigned to vehicle -> 403
    res = client.get(f"/api/v1/vehicles/{sample_vehicle.id}/taxes", headers=driver_headers)
    assert res.status_code == 403

    # Assign driver to vehicle
    assignment = VehicleAssignment(vehicle_id=sample_vehicle.id, driver_id=test_driver.id, is_active=True)
    db.add(assignment)
    db.commit()

    # Now assigned driver can read
    res_assigned = client.get(f"/api/v1/vehicles/{sample_vehicle.id}/taxes", headers=driver_headers)
    assert res_assigned.status_code == 200

    # Driver CANNOT create tax record -> 403
    payload = {
        "tax_type": "ROAD_TAX",
        "state": "Punjab",
        "amount": 10000.0,
        "period_start": str(today),
        "period_end": str(today + timedelta(days=365)),
        "valid_until": str(today + timedelta(days=365))
    }
    res_create = client.post(f"/api/v1/vehicles/{sample_vehicle.id}/taxes", json=payload, headers=driver_headers)
    assert res_create.status_code == 403


def test_government_charges_crud(client, admin_headers, sample_vehicle):
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
    res = client.post(f"/api/v1/vehicles/{sample_vehicle.id}/government-charges", json=payload, headers=admin_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["charge_type"] == "NATIONAL_PERMIT_FEE"
    charge_id = data["id"]

    # List Government Charges
    res_list = client.get(f"/api/v1/vehicles/{sample_vehicle.id}/government-charges", headers=admin_headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1

    # Delete Government Charge
    res_del = client.delete(f"/api/v1/vehicles/{sample_vehicle.id}/government-charges/{charge_id}", headers=admin_headers)
    assert res_del.status_code == 204


def test_challans_crud(client, admin_headers, sample_vehicle):
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
    res = client.post(f"/api/v1/vehicles/{sample_vehicle.id}/challans", json=payload, headers=admin_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["challan_number"] == "CH-PUN-00123"
    challan_id = data["id"]

    # Update Challan Status to PAID
    res_patch = client.patch(f"/api/v1/vehicles/{sample_vehicle.id}/challans/{challan_id}", json={"status": "PAID", "payment_date": str(today)}, headers=admin_headers)
    assert res_patch.status_code == 200
    assert res_patch.json()["status"] == "PAID"

    # List Challans
    res_list = client.get(f"/api/v1/vehicles/{sample_vehicle.id}/challans", headers=admin_headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1


def test_fastag_crud(client, admin_headers, sample_vehicle):
    # Initial fetch auto-creates record
    res_get = client.get(f"/api/v1/vehicles/{sample_vehicle.id}/fastag", headers=admin_headers)
    assert res_get.status_code == 200
    assert res_get.json()["vehicle_id"] == sample_vehicle.id

    # Update FASTag info
    payload = {
        "tag_number": "34161FFA0192837",
        "tag_provider": "ICICI Bank",
        "tag_status": "ACTIVE",
        "linked_account_ref": "ACC-998811",
        "last_balance": 3450.50,
        "notes": "Commercial fleet FASTag"
    }
    res_put = client.put(f"/api/v1/vehicles/{sample_vehicle.id}/fastag", json=payload, headers=admin_headers)
    assert res_put.status_code == 200
    data = res_put.json()
    assert data["tag_number"] == "34161FFA0192837"
    assert data["last_balance"] == 3450.50


def test_admin_fleet_queries_and_export(client, admin_headers, sample_vehicle):
    today = date.today()
    client.post(f"/api/v1/vehicles/{sample_vehicle.id}/taxes", json={
        "tax_type": "ROAD_TAX",
        "state": "Punjab",
        "amount": 30000.0,
        "period_start": str(today),
        "period_end": str(today + timedelta(days=365)),
        "payment_date": str(today),
        "valid_until": str(today + timedelta(days=365))
    }, headers=admin_headers)

    # Fleet taxes
    res_fleet = client.get("/api/v1/admin/taxes", headers=admin_headers)
    assert res_fleet.status_code == 200
    assert len(res_fleet.json()) >= 1

    # Excel export
    res_export = client.get("/api/v1/admin/taxes/export", headers=admin_headers)
    assert res_export.status_code == 200
    assert res_export.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert len(res_export.content) > 0


def test_admin_dashboard_metrics_includes_tax(client, admin_headers):
    res = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "active_taxes" in data
    assert "taxes_due_soon" in data
    assert "taxes_overdue" in data
    assert "taxes_expired" in data
