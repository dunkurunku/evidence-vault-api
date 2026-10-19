"""Pruebas contra una base de datos SQLite temporal, sin tocar PostgreSQL."""

import os
import tempfile

import pytest

# La configuración se lee al importar la app, así que se fija antes.
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["STORAGE_DIR"] = f"{_tmp}/storage"
os.environ["JWT_SECRET"] = "secreto-de-pruebas"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    """Registra un usuario y devuelve la cabecera Authorization lista para usar."""
    email = "ana@example.com"
    client.post("/auth/register", json={"email": email, "password": "contraseña-larga"})
    r = client.post("/auth/login", data={"username": email, "password": "contraseña-larga"})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
