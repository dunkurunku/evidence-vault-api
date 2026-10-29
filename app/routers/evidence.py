import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.config import get_settings
from app.db import get_db
from app.deps import get_current_user
from app.models import CustodyEvent, Evidence, User, utcnow
from app.services.custody import GENESIS, event_hash, first_broken_event
from app.services.hashing import sha256_of_stream
from app.services.summarizer import summarize

router = APIRouter(prefix="/evidence", tags=["evidence"])


def _get_owned(db: Session, user: User, evidence_id: int) -> Evidence:
    # 404 también si es de otro usuario, para no revelar que existe
    evidence = db.get(Evidence, evidence_id)
    if evidence is None or evidence.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evidencia no encontrada")
    return evidence


def _log(db: Session, evidence: Evidence, user: User, action: str, detail: Optional[str] = None):
    # flush para tener evidence.id antes de calcular el hash
    db.flush()
    prev_hash = evidence.events[-1].hash if evidence.events else GENESIS
    at = utcnow()
    digest = event_hash(prev_hash, evidence.id, user.id, action, detail, at)
    db.add(
        CustodyEvent(
            evidence=evidence,
            actor_id=user.id,
            action=action,
            detail=detail,
            at=at,
            prev_hash=prev_hash,
            hash=digest,
        )
    )


@router.post("", response_model=schemas.EvidenceOut, status_code=status.HTTP_201_CREATED)
def register_evidence(
    file: UploadFile, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> Evidence:
    """Guarda el fichero, calcula su SHA-256 y anota 'registered' en la cadena de custodia."""
    sha256 = sha256_of_stream(file.file)

    folder = Path(get_settings().storage_dir) / str(user.id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / uuid.uuid4().hex
    with path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    evidence = Evidence(
        owner_id=user.id,
        filename=file.filename or "sin-nombre",
        content_type=file.content_type or "application/octet-stream",
        size_bytes=path.stat().st_size,
        sha256=sha256,
        stored_path=str(path),
    )
    db.add(evidence)
    _log(db, evidence, user, "registered", f"sha256={sha256}")
    db.commit()
    db.refresh(evidence)
    return evidence


@router.get("", response_model=list[schemas.EvidenceOut])
def list_evidence(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[Evidence]:
    """Lista las evidencias del usuario autenticado, de más reciente a más antigua."""
    query = (
        select(Evidence)
        .where(Evidence.owner_id == user.id)
        .order_by(Evidence.registered_at.desc(), Evidence.id.desc())
    )
    return list(db.scalars(query))


@router.get("/{evidence_id}", response_model=schemas.EvidenceOut)
def get_evidence(
    evidence_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> Evidence:
    """Devuelve una evidencia con su cadena de custodia. 404 si no existe o no es del usuario."""
    return _get_owned(db, user, evidence_id)


@router.get("/{evidence_id}/custody", response_model=schemas.ChainCheck)
def check_custody(
    evidence_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> schemas.ChainCheck:
    """Recalcula la huella de cada evento y dice si la cadena de custodia sigue intacta."""
    evidence = _get_owned(db, user, evidence_id)
    broken = first_broken_event(evidence.events)
    return schemas.ChainCheck(
        evidence_id=evidence.id,
        valid=broken is None,
        events=len(evidence.events),
        broken_at=broken,
    )


@router.post("/{evidence_id}/verify", response_model=schemas.VerifyResult)
def verify_evidence(
    evidence_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> schemas.VerifyResult:
    """Recalcula la huella del fichero recibido y la compara con la registrada. Anota 'verified'."""
    evidence = _get_owned(db, user, evidence_id)
    received = sha256_of_stream(file.file)
    matches = received == evidence.sha256

    _log(db, evidence, user, "verified", "coincide" if matches else f"no coincide: {received}")
    db.commit()
    return schemas.VerifyResult(
        evidence_id=evidence.id,
        matches=matches,
        expected_sha256=evidence.sha256,
        received_sha256=received,
    )


@router.post("/{evidence_id}/summary", response_model=schemas.EvidenceOut)
def summarize_evidence(
    evidence_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> Evidence:
    """Pide a Claude un resumen del documento (solo texto), lo guarda y anota 'summarized'."""
    evidence = _get_owned(db, user, evidence_id)
    if not evidence.content_type.startswith("text/"):
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Solo se pueden resumir documentos de texto"
        )

    text = Path(evidence.stored_path).read_text(encoding="utf-8", errors="replace")
    try:
        evidence.summary = summarize(text)
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    _log(db, evidence, user, "summarized")
    db.commit()
    db.refresh(evidence)
    return evidence
