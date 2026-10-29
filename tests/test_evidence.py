import hashlib
import io

from sqlalchemy import select

CONTENIDO = b"Acta de la reunion del 3 de marzo. Asisten dos personas."
SHA = hashlib.sha256(CONTENIDO).hexdigest()


def _subir(client, headers, contenido=CONTENIDO, nombre="acta.txt"):
    return client.post(
        "/evidence",
        headers=headers,
        files={"file": (nombre, io.BytesIO(contenido), "text/plain")},
    )


def test_register_evidence_returns_sha256_and_first_event(client, auth_headers):
    r = _subir(client, auth_headers)
    assert r.status_code == 201
    body = r.json()
    assert body["sha256"] == SHA
    assert body["filename"] == "acta.txt"
    assert body["size_bytes"] == len(CONTENIDO)
    assert [e["action"] for e in body["events"]] == ["registered"]


def test_register_requires_auth(client):
    assert _subir(client, {}).status_code == 401


def test_list_and_get_only_own_evidence(client, auth_headers):
    _subir(client, auth_headers)
    r = client.get("/evidence", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) == 1
    evidence_id = r.json()[0]["id"]

    # otro usuario no debe verla
    client.post("/auth/register", json={"email": "otro@example.com", "password": "12345678x"})
    login = {"username": "otro@example.com", "password": "12345678x"}
    tok = client.post("/auth/login", data=login).json()
    otros = {"Authorization": f"Bearer {tok['access_token']}"}
    assert client.get("/evidence", headers=otros).json() == []
    assert client.get(f"/evidence/{evidence_id}", headers=otros).status_code == 404


def test_verify_detects_tampering(client, auth_headers):
    evidence_id = _subir(client, auth_headers).json()["id"]

    ok = client.post(
        f"/evidence/{evidence_id}/verify",
        headers=auth_headers,
        files={"file": ("acta.txt", io.BytesIO(CONTENIDO), "text/plain")},
    )
    assert ok.status_code == 200 and ok.json()["matches"] is True

    alterado = client.post(
        f"/evidence/{evidence_id}/verify",
        headers=auth_headers,
        files={"file": ("acta.txt", io.BytesIO(CONTENIDO + b"!"), "text/plain")},
    )
    assert alterado.status_code == 200 and alterado.json()["matches"] is False

    eventos = client.get(f"/evidence/{evidence_id}", headers=auth_headers).json()["events"]
    assert [e["action"] for e in eventos] == ["registered", "verified", "verified"]


def test_summary_uses_summarizer(client, auth_headers, monkeypatch):
    from app.routers import evidence as evidence_router

    monkeypatch.setattr(evidence_router, "summarize", lambda text: "Resumen de prueba.")
    evidence_id = _subir(client, auth_headers).json()["id"]
    r = client.post(f"/evidence/{evidence_id}/summary", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["summary"] == "Resumen de prueba."
    assert r.json()["events"][-1]["action"] == "summarized"


def test_summary_rejects_binary_files(client, auth_headers):
    r = client.post(
        "/evidence",
        headers=auth_headers,
        files={"file": ("foto.jpg", io.BytesIO(b"\xff\xd8\xff"), "image/jpeg")},
    )
    r = client.post(f"/evidence/{r.json()['id']}/summary", headers=auth_headers)
    assert r.status_code == 415


def test_summary_without_api_key_returns_503(client, auth_headers, monkeypatch):
    from app.routers import evidence as evidence_router

    def sin_clave(text):
        raise RuntimeError("Falta ANTHROPIC_API_KEY en el entorno")

    monkeypatch.setattr(evidence_router, "summarize", sin_clave)
    evidence_id = _subir(client, auth_headers).json()["id"]
    r = client.post(f"/evidence/{evidence_id}/summary", headers=auth_headers)
    assert r.status_code == 503
    eventos = client.get(f"/evidence/{evidence_id}", headers=auth_headers).json()["events"]
    assert [e["action"] for e in eventos] == ["registered"]


def test_custody_events_are_chained(client, auth_headers):
    evidence_id = _subir(client, auth_headers).json()["id"]
    client.post(
        f"/evidence/{evidence_id}/verify",
        headers=auth_headers,
        files={"file": ("acta.txt", io.BytesIO(CONTENIDO), "text/plain")},
    )
    eventos = client.get(f"/evidence/{evidence_id}", headers=auth_headers).json()["events"]
    assert eventos[0]["prev_hash"] == "0" * 64
    assert eventos[1]["prev_hash"] == eventos[0]["hash"]

    r = client.get(f"/evidence/{evidence_id}/custody", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == {"evidence_id": evidence_id, "valid": True, "events": 2, "broken_at": None}


def test_custody_detects_tampering_in_database(client, auth_headers):
    evidence_id = _subir(client, auth_headers).json()["id"]
    for _ in range(2):
        client.post(
            f"/evidence/{evidence_id}/verify",
            headers=auth_headers,
            files={"file": ("acta.txt", io.BytesIO(CONTENIDO), "text/plain")},
        )

    # simula que alguien edita un evento directamente en la BD
    from app.db import SessionLocal
    from app.models import CustodyEvent

    with SessionLocal() as db:
        evento = db.scalars(
            select(CustodyEvent)
            .where(CustodyEvent.evidence_id == evidence_id)
            .order_by(CustodyEvent.id)
        ).all()[1]
        evento.detail = "no coincide: alterado a mano"
        db.commit()

    r = client.get(f"/evidence/{evidence_id}/custody", headers=auth_headers)
    assert r.json()["valid"] is False
    assert r.json()["broken_at"] == 1
