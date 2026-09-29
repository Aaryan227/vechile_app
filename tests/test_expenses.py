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
