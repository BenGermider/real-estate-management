def test_compare_requires_ids(client, auth_token):
    resp = client.get("/compare/regions", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 400


def test_compare_success(client, auth_token, seeded_metrics):
    resp = client.get("/compare/regions?region_ids=06037", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["regions"]) == 1
    assert body["regions"][0]["region_id"] == "06037"

