"""FastAPI application factory. Run (from backend/): uvicorn app.main:create_app --factory --reload"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.deps import Container, build_container
from app.api.v1 import catalog, commerce, health, identifications, identify
from app.core.config import Settings, get_settings
from app.core.errors import ImageTooLargeError, error_body, install_error_handlers
from app.core.logging import configure_logging

logger = logging.getLogger("app.request")
API_PREFIX = "/api/v1"
API_VERSION = "0.1.0"


def create_app(settings: Settings | None = None, container: Container | None = None) -> FastAPI:
    settings = settings or (container.settings if container else get_settings())
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.container = container or build_container(settings)
        try:
            app.state.container.snapshots.get()  # fail fast on a broken catalog
            yield
        finally:
            app.state.container.close()

    app = FastAPI(
        title=f"{settings.app_name} API",
        version=API_VERSION,
        description="Identification of aquatic organisms and artificial flies for fly fishing. "
        "Similarity scores are not probabilities; see docs/AI_PIPELINE.md.",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url=None,
    )
    if container is not None:
        app.state.container = container
    install_error_handlers(app)

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["GET", "POST"],
            allow_headers=["Content-Type", "Accept-Language", "X-Client-Id"],
        )

    # Reject oversized uploads before reading the body (multipart overhead allowance: 1 MB).
    max_body = settings.max_upload_bytes + 1024 * 1024

    @app.middleware("http")
    async def guard_and_log(request: Request, call_next):
        started = time.monotonic()
        length = request.headers.get("content-length")
        if request.method == "POST" and length and length.isdigit() and int(length) > max_body:
            error = ImageTooLargeError(f"Request exceeds the {settings.max_upload_mb} MB limit.")
            return JSONResponse(status_code=error.status_code, content=error_body(error.code, error.message))
        response = await call_next(request)
        # Path and status only: no query strings, headers, bodies or client ids.
        logger.info("%s %s %s %dms", request.method, request.url.path, response.status_code, (time.monotonic() - started) * 1000)
        return response

    v1 = APIRouter(prefix=API_PREFIX)
    for module in (health, identify, catalog, commerce, identifications):
        v1.include_router(module.router)
    app.include_router(v1)
    return app
