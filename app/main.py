from pathlib import Path

from fastapi import FastAPI

from app.config import get_settings
from app.db import Base, engine
from app.routers import auth, evidence

app = FastAPI(
    title="Evidence Vault API",
    version="0.1.0",
    description="Custodia de ficheros con huella SHA-256, cadena de custodia y resumen con IA.",
)
app.include_router(auth.router)
app.include_router(evidence.router)


@app.on_event("startup")
def startup() -> None:
    # TODO: migraciones con Alembic
    Base.metadata.create_all(bind=engine)
    Path(get_settings().storage_dir).mkdir(parents=True, exist_ok=True)


@app.get("/health", tags=["system"])
def health() -> dict:
    return {"status": "ok"}
