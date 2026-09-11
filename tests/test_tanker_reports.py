def test_create_tanker_report_and_auto_calculate(client, master_headers, admin_headers):
    # Create a vehicle first as Master
    v_res = client.post("/api/v1/vehicles", headers=master_headers, json={
        "vehicle_number": "MH04TR1234",
        "vehicle_class": "Tanker"
    })
    assert v_res.status_code == 201
    vehicle_id = v_res.json()["id"]

    # Admin trying to create tanker report should be forbidden (read-only monitor)
    admin_try = client.post("/api/v1/tanker-reports", headers=admin_headers, json={
        "report_date": "2026-08-23",
        "vehicle_id": vehicle_id,
        "ul_point": "Pakuria KSK",
        "rtkm": 265.6,
        "rate": 3.559476
    })
    assert admin_try.status_code == 403

    # Master submits tanker report entry
    report_res = client.post("/api/v1/tanker-reports", headers=master_headers, json={
        "report_date": "2026-08-23",
        "vehicle_id": vehicle_id,
        "ul_point": "Pakuria KSK",
        "rtkm": 265.6,
        "rate": 3.559476,
        "pump": "Pakuria KSK",
        "hsd_ltr": 50.0,
        "hsd_rate": 90.0,
        "khuraki": 500.0
    })
    assert report_res.status_code == 201
    data = report_res.json()
    assert data["freight"] == round(265.6 * 3.559476, 2)
    assert data["hsd_amount"] == 4500.0
    assert data["khuraki"] == 500.0

def test_export_tanker_reports_excel(client, master_headers, admin_headers):
    # Both master and admin can export/read
    response = client.get("/api/v1/tanker-reports/export", headers=admin_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    m_response = client.get("/api/v1/tanker-reports/export", headers=master_headers)
    assert m_response.status_code == 200

