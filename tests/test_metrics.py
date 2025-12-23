def test_metrics_not_found(client, auth_token):
    resp = client.get("/metrics/region/99999", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 404


def test_metrics_success(client, auth_token, seeded_metrics):
    resp = client.get("/metrics/region/06037", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["region_id"] == "06037"
    assert body["median_household_income"] == 80000


def test_timeseries(client, auth_token, seeded_metrics):
    resp = client.get("/metrics/region/06037/timeseries", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["region_id"] == "06037"
    assert len(body["series"]) >= 1

