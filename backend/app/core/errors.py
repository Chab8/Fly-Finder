"""Application error hierarchy and consistent JSON error responses."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base error. `code` is a stable machine-readable identifier used by the mobile app."""

    status_code = 400
    code = "bad_request"

    def __init__(self, message: str, *, code: str | None = None, details: dict | None = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        self.details = details or {}


class InvalidImageError(AppError):
    status_code = 422
    code = "invalid_image"


class ImageTooLargeError(AppError):
    status_code = 413
    code = "image_too_large"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class RateLimitedError(AppError):
    status_code = 429
    code = "rate_limited"


class ProviderUnavailableError(AppError):
    """An external provider (Gemini, GBIF, DB...) is down, slow or not configured."""

    status_code = 503
    code = "provider_unavailable"

    def __init__(self, provider: str, message: str, *, code: str | None = None):
        super().__init__(message, code=code, details={"provider": provider})
        self.provider = provider


class ProviderResponseError(AppError):
    """A provider answered, but its payload did not match the expected schema."""

    status_code = 502
    code = "provider_bad_response"

    def __init__(self, provider: str, message: str):
        super().__init__(message, details={"provider": provider})
        self.provider = provider


def error_body(code: str, message: str, details: dict | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or {}}}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        retry_after = exc.details.get("retry_after_seconds") if exc.details else None
        headers = {"Retry-After": str(retry_after)} if retry_after else None
        return JSONResponse(status_code=exc.status_code, content=error_body(exc.code, exc.message, exc.details), headers=headers)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        # Only expose field locations and messages, never the submitted values.
        errors = [{"loc": list(e.get("loc", [])), "msg": e.get("msg", "")} for e in exc.errors()]
        return JSONResponse(status_code=422, content=error_body("validation_error", "Invalid request", {"errors": errors}))

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "not_found" if exc.status_code == 404 else "http_error"
        return JSONResponse(status_code=exc.status_code, content=error_body(code, str(exc.detail)))

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", type(exc).__name__)
        return JSONResponse(status_code=500, content=error_body("internal_error", "Unexpected server error"))
