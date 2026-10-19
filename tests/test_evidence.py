"""Pruebas de la bóveda. Están marcadas como pendientes: quita el decorador `pendiente`
de cada una a medida que implementes el endpoint en app/routers/evidence.py."""

import hashlib
import io

import pytest

pendiente = pytest.mark.skip(reason="endpoint pendiente de implementar")

CONTENIDO = b"Acta de la reunion del 3 de marzo. Asisten dos personas."
SHA = hashlib.sha256(CONTENIDO).hexdigest()


def _subir(client, headers, contenido=CONTENIDO, nombre="acta.txt"):
    return client.post(
        "/evidence",
        headers=headers,
        files={"file": (nombre, io.BytesIO(contenido), "text/plain")},
    )


@pendiente
def test_register_evidence_returns_sha256_and_first_event(client, auth_headers):
    r = _subir(client, auth_headers)
    assert r.status_code == 201
    body = r.json()
    assert body["sha256"] == SHA
    assert body["filename"] == "acta.txt"
    assert body["size_bytes"] == len(CONTENIDO)
    assert [e["action"] for e in body["events"]] == ["registered"]


@pendiente
def test_register_requires_auth(client):
    assert _subir(client, {}).status_code == 401


@pendiente
def test_list_and_get_only_own_evidence(client, auth_headers):
    _subir(client, auth_headers)
    r = client.get("/evidence", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) == 1
    evidence_id = r.json()[0]["id"]

    # Otro usuario no debe ver ni esa lista ni ese elemento.
    client.post("/auth/register", json={"email": "otro@example.com", "password": "12345678x"})
    login = {"username": "otro@example.com", "password": "12345678x"}
    tok = client.post("/auth/login", data=login).json()
    otros = {"Authorization": f"Bearer {tok['access_token']}"}
    assert client.get("/evidence", headers=otros).json() == []
    assert client.get(f"/evidence/{evidence_id}", headers=otros).status_code == 404


@pendiente
def test_verify_detects_tampering(client, auth_headers):
    evidence_id = _subir(client, auth_headers).json()["id"]

    ok = client.post(
        f"/evidence/{evidence_id}/verify", headers=auth_headers,
        files={"file": ("acta.txt", io.BytesIO(CONTENIDO), "text/plain")},
    )
    assert ok.status_code == 200 and ok.json()["matches"] is True

    alterado = client.post(
        f"/evidence/{evidence_id}/verify", headers=auth_headers,
        files={"file": ("acta.txt", io.BytesIO(CONTENIDO + b"!"), "text/plain")},
    )
    assert alterado.status_code == 200 and alterado.json()["matches"] is False

    eventos = client.get(f"/evidence/{evidence_id}", headers=auth_headers).json()["events"]
    assert [e["action"] for e in eventos] == ["registered", "verified", "verified"]


@pendiente
def test_summary_uses_summarizer(client, auth_headers, monkeypatch):
    # No se llama a la API real: se sustituye la función por una fija.
    from app.routers import evidence as evidence_router

    monkeypatch.setattr(evidence_router, "summarize", lambda text: "Resumen de prueba.")
    evidence_id = _subir(client, auth_headers).json()["id"]
    r = client.post(f"/evidence/{evidence_id}/summary", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["summary"] == "Resumen de prueba."
    assert r.json()["events"][-1]["action"] == "summarized"
