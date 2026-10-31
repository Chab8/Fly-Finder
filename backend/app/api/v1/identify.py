from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile

from app.api.deps import Container, get_client_hash, get_container, get_language
from app.core.errors import ImageTooLargeError
from app.schemas.identification import FlyIdentificationResponse, OrganismIdentificationResponse
from app.services.identification.common import IdentificationContext

router = APIRouter(prefix="/identify", tags=["identification"])

_CHUNK = 1024 * 1024


def _read_limited(upload: UploadFile, max_bytes: int) -> bytes:
    """Read the upload without ever holding more than max_bytes + 1 chunk in memory."""
    data = bytearray()
    while chunk := upload.file.read(_CHUNK):
        data.extend(chunk)
        if len(data) > max_bytes:
            raise ImageTooLargeError(f"Image exceeds the {max_bytes // (1024 * 1024)} MB limit.")
    return bytes(data)


def _prepare(request: Request, container: Container, client_hash: str | None) -> None:
    client_ip = request.client.host if request.client else "unknown"
    container.rate_limiter.check(client_hash or client_ip)


@router.post(
    "/organism",
    response_model=OrganismIdentificationResponse,
    summary="Identify a real organism and recommend imitating flies",
    responses={413: {"description": "Image too large"}, 422: {"description": "Invalid image"}, 429: {"description": "Rate limited"}, 503: {"description": "Analysis unavailable"}},
)
def identify_organism(
    request: Request,
    image: UploadFile = File(..., description="JPEG, PNG, WEBP or HEIC photo"),
    store_image: bool = Form(False, description="User consent to keep the photo (only honoured if the server allows it)"),
    container: Container = Depends(get_container),
    lang: str = Depends(get_language),
    client_hash: str | None = Depends(get_client_hash),
) -> OrganismIdentificationResponse:
    _prepare(request, container, client_hash)
    data = _read_limited(image, container.settings.max_upload_bytes)
    ctx = IdentificationContext(lang=lang, client_hash=client_hash, store_image=store_image)
    return container.organism_service.identify(data, ctx)


@router.post(
    "/fly",
    response_model=FlyIdentificationResponse,
    summary="Identify an artificial fly and what it imitates",
    responses={413: {"description": "Image too large"}, 422: {"description": "Invalid image"}, 429: {"description": "Rate limited"}, 503: {"description": "Analysis unavailable"}},
)
def identify_fly(
    request: Request,
    image: UploadFile = File(..., description="JPEG, PNG, WEBP or HEIC photo"),
    store_image: bool = Form(False),
    country: str | None = Query(None, pattern=r"^[A-Za-z]{2}$", description="ISO country, to rank stores that ship there"),
    container: Container = Depends(get_container),
    lang: str = Depends(get_language),
    client_hash: str | None = Depends(get_client_hash),
) -> FlyIdentificationResponse:
    _prepare(request, container, client_hash)
    data = _read_limited(image, container.settings.max_upload_bytes)
    ctx = IdentificationContext(lang=lang, client_hash=client_hash, store_image=store_image)
    return container.fly_service.identify(data, ctx, country=country.upper() if country else None)
