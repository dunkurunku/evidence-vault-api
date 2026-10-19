"""Bóveda de evidencias.

Estos endpoints están por implementar. Cada uno tiene su prueba en tests/test_evidence.py,
marcada como pendiente: quita la marca cuando lo implementes y la prueba te dirá si funciona.

Piezas ya disponibles para usarlas aquí:
  - app.services.hashing.sha256_of_stream(fichero)  -> huella SHA-256
  - app.services.summarizer.summarize(texto)         -> resumen con Claude
  - app.models.Evidence y app.models.CustodyEvent     -> tablas
  - get_current_user                                   -> usuario autenticado
  - get_settings().storage_dir                         -> carpeta donde guardar los ficheros
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app import schemas
from app.db import get_db
from app.deps import get_current_user
from app.models import User

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.post("", response_model=schemas.EvidenceOut, status_code=status.HTTP_201_CREATED)
def register_evidence(
    file: UploadFile, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """Guarda el fichero, calcula su SHA-256 y anota 'registered' en la cadena de custodia."""
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Pendiente de implementar")


@router.get("", response_model=list[schemas.EvidenceOut])
def list_evidence(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Lista las evidencias del usuario autenticado, de más reciente a más antigua."""
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Pendiente de implementar")


@router.get("/{evidence_id}", response_model=schemas.EvidenceOut)
def get_evidence(
    evidence_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """Devuelve una evidencia con su cadena de custodia. 404 si no existe o no es del usuario."""
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Pendiente de implementar")


@router.post("/{evidence_id}/verify", response_model=schemas.VerifyResult)
def verify_evidence(
    evidence_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Recalcula la huella del fichero recibido y la compara con la registrada. Anota 'verified'."""
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Pendiente de implementar")


@router.post("/{evidence_id}/summary", response_model=schemas.EvidenceOut)
def summarize_evidence(
    evidence_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """Pide a Claude un resumen del documento (solo texto), lo guarda y anota 'summarized'."""
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Pendiente de implementar")
