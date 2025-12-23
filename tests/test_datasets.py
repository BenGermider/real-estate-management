from backend.app.models import Dataset


def test_list_datasets(client, auth_token):
    resp = client.get("/datasets", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert body["total"] >= 0


def test_get_dataset_success(client, auth_token):
    resp = client.get("/datasets/acs", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "acs"


def test_get_dataset_not_found(client, auth_token):
    resp = client.get("/datasets/missing", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 404

