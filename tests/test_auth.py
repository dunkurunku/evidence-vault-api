def test_register_login_me(client):
    r = client.post("/auth/register", json={"email": "luis@example.com", "password": "12345678x"})
    assert r.status_code == 201
    assert r.json()["email"] == "luis@example.com"

    r = client.post("/auth/login", data={"username": "luis@example.com", "password": "12345678x"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "luis@example.com"


def test_register_duplicate_email(client):
    body = {"email": "dup@example.com", "password": "12345678x"}
    assert client.post("/auth/register", json=body).status_code == 201
    assert client.post("/auth/register", json=body).status_code == 409


def test_login_wrong_password(client):
    client.post("/auth/register", json={"email": "p@example.com", "password": "12345678x"})
    r = client.post("/auth/login", data={"username": "p@example.com", "password": "mala"})
    assert r.status_code == 401


def test_me_without_token(client):
    assert client.get("/auth/me").status_code == 401


def test_me_with_garbage_token(client):
    assert client.get("/auth/me", headers={"Authorization": "Bearer basura"}).status_code == 401
