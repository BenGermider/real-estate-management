from backend.app.models import Region


def test_regions_empty(client, auth_token):
    resp = client.get("/regions", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 0


def test_regions_with_seed(client, auth_token, seeded_region):
    resp = client.get("/regions?state_fips=06", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert any(item["region_id"] == "06037" for item in body["items"])

