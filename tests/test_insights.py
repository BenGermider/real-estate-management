def test_insights_not_found(client, auth_token):
    resp = client.get("/insights/region/99999", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 404


def test_insights_success(client, auth_token, seeded_metrics):
    resp = client.get("/insights/region/06037", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["region_id"] == "06037"
    assert "affordability_quartile" in body

