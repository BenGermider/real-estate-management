def test_login_success(client):
    resp = client.post("/auth/login", json={"email": "admin@example.com", "password": "Password123!"})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "Bearer"


def test_login_invalid(client):
    resp = client.post("/auth/login", json={"email": "admin@example.com", "password": "wrong"})
    assert resp.status_code == 401


def test_me_requires_auth(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_success(client, auth_token):
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "admin@example.com"

