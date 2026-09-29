def test_profit_loss_calculation(client, master_headers):
    # 1. Create firm and vehicle
    f_res = client.post("/api/v1/firms", headers=master_headers, json={"name": "Profit Test Firm"})
    firm_id = f_res.json()["id"]

    v_res = client.post("/api/v1/vehicles", headers=master_headers, json={
        "vehicle_number": "WB22PL1000",
        "vehicle_class": "Tanker",
        "firm_id": firm_id
    })
    vehicle_id = v_res.json()["id"]

    # 2. Add Tanker Trip (Income)
    # RTKM: 300, Rate: 50 -> Freight: 15,000
    t_res = client.post("/api/v1/tanker-reports", headers=master_headers, json={
        "report_date": "2026-09-29",
        "vehicle_id": vehicle_id,
        "ul_point": "Kolkata Terminal",
        "rtkm": 300.0,
        "rate": 50.0,
        "hsd_ltr": 0.0,
        "hsd_rate": 0.0,
        "khuraki": 0.0
    })
    assert t_res.status_code == 201
    assert t_res.json()["freight"] == 15000.0

    # 3. Add Expenses (Expenditure)
    # Tyre: 4000, Toll: 1000 -> Total: 5,000
    client.post("/api/v1/expenses", headers=master_headers, json={
        "vehicle_id": vehicle_id,
        "expense_date": "2026-09-29",
        "category": "tyre",
        "amount": 4000.0
    })
    client.post("/api/v1/expenses", headers=master_headers, json={
        "vehicle_id": vehicle_id,
        "expense_date": "2026-09-29",
        "category": "toll",
        "amount": 1000.0
    })

    # 4. Query Profit / Loss endpoint
    pl_res = client.get(f"/api/v1/financials/profit-loss?vehicle_id={vehicle_id}&date_from=2026-09-29&date_to=2026-09-29", headers=master_headers)
    assert pl_res.status_code == 200
    data = pl_res.json()
    assert data["total_income"] == 15000.0
    assert data["total_expenditure"] == 5000.0
    # Income - Expenditure = Profit
    assert data["net_profit"] == 10000.0
    assert data["profit_status"] == "PROFIT"
    assert data["category_breakdown"]["tyre"] == 4000.0
    assert data["category_breakdown"]["toll"] == 1000.0

    # 5. Query Log Book
    lb_res = client.get(f"/api/v1/financials/log-book?vehicle_id={vehicle_id}", headers=master_headers)
    assert lb_res.status_code == 200
    entries = lb_res.json()["entries"]
    assert len(entries) >= 3  # 1 trip + 2 expenses

    # 6. Export Log Book to Excel
    exp_res = client.get(f"/api/v1/financials/export?vehicle_id={vehicle_id}", headers=master_headers)
    assert exp_res.status_code == 200
    assert exp_res.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
