def test_create_and_filter_expenses(client, master_headers):
    # Create firm & vehicle
    f_res = client.post("/api/v1/firms", headers=master_headers, json={"name": "Express Logistics"})
    firm_id = f_res.json()["id"]

    v_res = client.post("/api/v1/vehicles", headers=master_headers, json={
        "vehicle_number": "WB19XX5555",
        "vehicle_class": "Tanker",
        "firm_id": firm_id
    })
    vehicle_id = v_res.json()["id"]

    # Log expenses under different categories
    categories = ["tyre", "battery", "maintenance", "salary", "khuraki", "toll", "road_tax", "others"]
    for cat in categories:
        exp_res = client.post("/api/v1/expenses", headers=master_headers, json={
            "vehicle_id": vehicle_id,
            "expense_date": "2026-09-29",
            "category": cat,
            "amount": 1500.0,
            "description": f"Test {cat} cost"
        })
        assert exp_res.status_code == 201
        assert exp_res.json()["category"] == cat
        assert exp_res.json()["vehicle_number"] == "WB19XX5555"

    # Filter by category
    filter_res = client.get(f"/api/v1/expenses?vehicle_id={vehicle_id}&category=tyre", headers=master_headers)
    assert filter_res.status_code == 200
    tyre_expenses = filter_res.json()
    assert len(tyre_expenses) == 1
    assert tyre_expenses[0]["category"] == "tyre"


def test_fastag_toll_auto_deduction_and_warning(client, master_headers):
    # 1. Setup firm and vehicle
    f_res = client.post("/api/v1/firms", headers=master_headers, json={"name": "FASTag Logistics Co"})
    firm_id = f_res.json()["id"]

    v_res = client.post("/api/v1/vehicles", headers=master_headers, json={
        "vehicle_number": "DL01FT2000",
        "vehicle_class": "Tanker",
        "firm_id": firm_id
    })
    vehicle_id = v_res.json()["id"]

    # 2. Set FASTag initial balance = ₹2000.00
    tag_res = client.put(f"/api/v1/vehicles/{vehicle_id}/fastag", headers=master_headers, json={
        "tag_number": "TAG2000XYZ",
        "tag_provider": "ICICI Bank",
        "tag_status": "ACTIVE",
        "last_balance": 2000.0
    })
    assert tag_res.status_code == 200
    assert tag_res.json()["last_balance"] == 2000.0

    # 3. Log a normal toll expense: ₹500
    exp1 = client.post("/api/v1/expenses", headers=master_headers, json={
        "vehicle_id": vehicle_id,
        "expense_date": "2026-10-06",
        "category": "toll",
        "amount": 500.0,
        "description": "Toll plaza #1"
    })
    assert exp1.status_code == 201
    assert exp1.json()["fastag_balance"] == 1500.0
    assert exp1.json()["fastag_warning"] is None

    # Verify FASTag state in DB
    tag_check1 = client.get(f"/api/v1/vehicles/{vehicle_id}/fastag", headers=master_headers)
    assert tag_check1.json()["last_balance"] == 1500.0
    assert tag_check1.json()["tag_status"] == "ACTIVE"

    # 4. Log a toll expense exceeding balance: ₹2000 (Remaining is 1500 -> goes to -500)
    exp2 = client.post("/api/v1/expenses", headers=master_headers, json={
        "vehicle_id": vehicle_id,
        "expense_date": "2026-10-06",
        "category": "toll",
        "amount": 2000.0,
        "description": "Heavy expressway toll"
    })
    assert exp2.status_code == 201
    assert exp2.json()["fastag_balance"] == -500.0
    assert exp2.json()["fastag_warning"] is not None
    assert "surpassed" in exp2.json()["fastag_warning"]
    assert "LOW BALANCE" in exp2.json()["fastag_warning"]
    exp2_id = exp2.json()["id"]

    # Verify FASTag updated to LOW_BALANCE
    tag_check2 = client.get(f"/api/v1/vehicles/{vehicle_id}/fastag", headers=master_headers)
    assert tag_check2.json()["last_balance"] == -500.0
    assert tag_check2.json()["tag_status"] == "LOW_BALANCE"

    # 5. Delete exp2 and verify balance is restored
    del_res = client.delete(f"/api/v1/expenses/{exp2_id}", headers=master_headers)
    assert del_res.status_code == 200

    tag_check3 = client.get(f"/api/v1/vehicles/{vehicle_id}/fastag", headers=master_headers)
    assert tag_check3.json()["last_balance"] == 1500.0
    assert tag_check3.json()["tag_status"] == "ACTIVE"

    # 6. Test updating an existing toll expense: change exp1 from 500 to 700
    exp1_id = exp1.json()["id"]
    upd_res = client.patch(f"/api/v1/expenses/{exp1_id}", headers=master_headers, json={"amount": 700.0})
    assert upd_res.status_code == 200
    tag_check4 = client.get(f"/api/v1/vehicles/{vehicle_id}/fastag", headers=master_headers)
    assert tag_check4.json()["last_balance"] == 1300.0

    # 7. Test switching category away from toll refunds the balance
    upd_cat = client.patch(f"/api/v1/expenses/{exp1_id}", headers=master_headers, json={"category": "maintenance"})
    assert upd_cat.status_code == 200
    tag_check5 = client.get(f"/api/v1/vehicles/{vehicle_id}/fastag", headers=master_headers)
    assert tag_check5.json()["last_balance"] == 2000.0

