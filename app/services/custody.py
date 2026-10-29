"""Cadena de custodia: cada evento guarda el hash del anterior.

Ojo: si se borra el último evento no se detecta.
"""

import hashlib
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Optional

GENESIS = "0" * 64


def _canonical_time(at: datetime) -> str:
    # sqlite devuelve las fechas sin tz, así que lo paso todo a UTC
    if at.tzinfo is not None:
        at = at.astimezone(timezone.utc).replace(tzinfo=None)
    return at.strftime("%Y-%m-%dT%H:%M:%S.%f")


def event_hash(
    prev_hash: str,
    evidence_id: int,
    actor_id: int,
    action: str,
    detail: Optional[str],
    at: datetime,
) -> str:
    fields = [prev_hash, str(evidence_id), str(actor_id), action, detail or "", _canonical_time(at)]
    return hashlib.sha256("|".join(fields).encode("utf-8")).hexdigest()


def first_broken_event(events: Sequence) -> Optional[int]:
    """Índice del primer evento roto, o None si la cadena está bien."""
    prev = GENESIS
    for i, e in enumerate(events):
        expected = event_hash(prev, e.evidence_id, e.actor_id, e.action, e.detail, e.at)
        if e.prev_hash != prev or e.hash != expected:
            return i
        prev = e.hash
    return None
