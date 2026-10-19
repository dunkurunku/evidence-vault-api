"""Esquemas de entrada y salida de la API (Pydantic)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CustodyEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    action: str
    detail: Optional[str]
    at: datetime


class EvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    content_type: str
    size_bytes: int
    sha256: str
    registered_at: datetime
    summary: Optional[str] = None
    events: list[CustodyEventOut] = []


class VerifyResult(BaseModel):
    evidence_id: int
    matches: bool
    expected_sha256: str
    received_sha256: str
