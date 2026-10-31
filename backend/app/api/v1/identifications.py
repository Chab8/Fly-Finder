from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import Container, get_client_hash, get_container
from app.core.errors import AppError, NotFoundError
from app.schemas.identification import IdentificationSummary

router = APIRouter(prefix="/identifications", tags=["identification"])


def _require_client(client_hash: str | None) -> str:
    if not client_hash:
        raise AppError("A valid X-Client-Id header is required to read history.", code="client_id_required")
    return client_hash


@router.get("", response_model=list[IdentificationSummary], summary="History of this device's identifications")
def list_identifications(
    limit: int = Query(20, ge=1, le=100),
    client_hash: str | None = Depends(get_client_hash),
    container: Container = Depends(get_container),
) -> list[IdentificationSummary]:
    records = container.identifications.list_for_client(_require_client(client_hash), limit)
    return [
        IdentificationSummary(
            id=r.id, kind=r.kind, created_at=r.created_at, match_level=r.match_level, primary_label=r.primary_label,
            image_stored=r.image_storage_path is not None, is_demo=r.is_demo,
        )
        for r in records
    ]


@router.get("/{identification_id}", summary="Stored result of one of this device's identifications")
def get_identification(
    identification_id: uuid.UUID,
    client_hash: str | None = Depends(get_client_hash),
    container: Container = Depends(get_container),
) -> dict[str, Any]:
    record = container.identifications.get_for_client(identification_id, _require_client(client_hash))
    if record is None:
        raise NotFoundError("Identification not found")
    return {**record.result, "identification_id": str(record.id)}
