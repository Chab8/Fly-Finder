from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.deps import Container, get_container

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
def health() -> dict:
    return {"status": "ok"}


@router.get("/ready", summary="Readiness: catalog loaded and provider configuration")
def ready(container: Container = Depends(get_container)) -> JSONResponse:
    """Reports configuration only. It never calls Gemini, so it costs no API credits."""
    settings = container.settings
    components: dict[str, dict] = {}
    ok = True
    try:
        snapshot = container.snapshots.get()
        components["catalog"] = {
            "status": "ok", "backend": settings.catalog_backend.value, "organisms": len(snapshot.organisms),
            "fly_patterns": len(snapshot.flies), "products": len(snapshot.products), "approved_images": len(snapshot.images_by_id),
        }
    except Exception as exc:  # report, do not crash
        ok = False
        components["catalog"] = {"status": "error", "error": type(exc).__name__}
    components["ai"] = {
        "status": "configured" if container.analyzer.available else "not_configured",
        "provider": container.analyzer.provider, "model": container.analyzer.model,
    }
    components["embeddings"] = {
        "status": "enabled" if container.embedder.available else "disabled", "model": container.embedder.model_id,
        "reason": getattr(container.embedder, "reason", None),
    }
    body = {
        "status": "ready" if ok else "not_ready", "environment": settings.environment.value,
        "demo_mode": settings.demo_mode, "components": components,
    }
    return JSONResponse(status_code=200 if ok else 503, content=body)
