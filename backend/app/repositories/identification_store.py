"""Identification log storage (interface + in-memory implementation)."""

from __future__ import annotations

import threading
import uuid
from collections import deque
from datetime import datetime
from typing import Any, Protocol

from pydantic import BaseModel, Field


class CandidateRow(BaseModel):
    position: int
    label: str
    organism_id: uuid.UUID | None = None
    fly_pattern_id: uuid.UUID | None = None
    ai_confidence: str | None = None
    visual_similarity: float | None = None


class IdentificationRecord(BaseModel):
    id: uuid.UUID
    client_hash: str | None
    kind: str
    match_level: str
    primary_label: str | None
    result: dict[str, Any]
    analysis_source: str
    ai_model: str | None
    embedding_model: str | None
    image_consent: bool = False
    image_storage_path: str | None = None
    is_demo: bool = False
    created_at: datetime
    candidates: list[CandidateRow] = Field(default_factory=list)


class IdentificationStore(Protocol):
    def save(self, record: IdentificationRecord) -> None: ...

    def list_for_client(self, client_hash: str, limit: int) -> list[IdentificationRecord]: ...

    def get_for_client(self, identification_id: uuid.UUID, client_hash: str) -> IdentificationRecord | None: ...


class InMemoryIdentificationStore:
    """Bounded, process-local log for development and tests. Lost on restart."""

    def __init__(self, max_records: int = 1000):
        self._records: deque[IdentificationRecord] = deque(maxlen=max_records)
        self._lock = threading.Lock()

    def save(self, record: IdentificationRecord) -> None:
        with self._lock:
            self._records.appendleft(record)

    def list_for_client(self, client_hash: str, limit: int) -> list[IdentificationRecord]:
        with self._lock:
            return [r for r in self._records if r.client_hash == client_hash][:limit]

    def get_for_client(self, identification_id: uuid.UUID, client_hash: str) -> IdentificationRecord | None:
        with self._lock:
            return next((r for r in self._records if r.id == identification_id and r.client_hash == client_hash), None)
