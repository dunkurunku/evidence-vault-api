import os
import tempfile

import pytest

# hay que fijarlo antes de importar la app
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["STORAGE_DIR"] = f"{_tmp}/storage"
os.environ["JWT_SECRET"] = "secreto-de-pruebas"

from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    email = "ana@example.com"
    client.post("/auth/register", json={"email": email, "password": "contraseña-larga"})
    r = client.post("/auth/login", data={"username": email, "password": "contraseña-larga"})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
