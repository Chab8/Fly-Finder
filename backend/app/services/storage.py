"""Supabase Storage client (REST API, service role key, server-side only)."""

from __future__ import annotations

import httpx

from app.core.errors import ProviderUnavailableError


class SupabaseStorage:
    def __init__(self, supabase_url: str, service_role_key: str, timeout_seconds: float = 20.0, http: httpx.Client | None = None):
        self._base = supabase_url.rstrip("/")
        # New secret keys (sb_secret_...) are not JWTs and go only in `apikey`.
        # Legacy service_role keys are JWTs and are also sent as a bearer token.
        headers = {"apikey": service_role_key}
        if not service_role_key.startswith("sb_"):
            headers["Authorization"] = f"Bearer {service_role_key}"
        self._http = http or httpx.Client(timeout=timeout_seconds, headers=headers)

    def upload(self, bucket: str, path: str, data: bytes, content_type: str, *, upsert: bool = False) -> str:
        url = f"{self._base}/storage/v1/object/{bucket}/{path.lstrip('/')}"
        headers = {"Content-Type": content_type, "x-upsert": "true" if upsert else "false"}
        try:
            response = self._http.post(url, content=data, headers=headers)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError("supabase_storage", "Image upload failed.") from exc
        return path

    def public_url(self, bucket: str, path: str) -> str:
        return f"{self._base}/storage/v1/object/public/{bucket}/{path.lstrip('/')}"
