def test_create_and_fetch_route_point(client, master_headers):
    # Add new loading/unloading point (e.g. from "+ Add More" modal)
    res = client.post("/api/v1/route-points", headers=master_headers, json={
        "name": "Durgapur Depot",
        "point_type": "UNLOADING",
        "default_rtkm": 340.5,
        "default_rate": 3.75,
        "pump_station": "Durgapur IOCL"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Durgapur Depot"
    assert data["default_rtkm"] == 340.5
    assert data["default_rate"] == 3.75

    # List route points to confirm it appears in dropdown options
    list_res = client.get("/api/v1/route-points", headers=master_headers)
    assert list_res.status_code == 200
    points = list_res.json()
    assert any(p["name"] == "Durgapur Depot" for p in points)
