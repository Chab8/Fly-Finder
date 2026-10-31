"""iNaturalist API v1 client, used by catalog tooling only (never at identification time).

Docs: https://www.inaturalist.org/pages/api+reference and https://api.inaturalist.org/v1/docs/
- No key needed for read-only requests.
- iNaturalist asks clients to stay around 1 request/second (and well under 10k/day),
  and to send an identifying User-Agent. This client enforces 1 req/s.
- Public API access does NOT include the iNaturalist computer-vision model.
- Every photo carries its own license_code (null = all rights reserved).
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.errors import ProviderUnavailableError
from app.services.taxonomy.licenses import COMMERCIAL_OK, commercial_use_allowed, license_label

_MIN_INTERVAL_SECONDS = 1.0


@dataclass(frozen=True)
class PhotoCandidate:
    taxon_name: str
    photo_id: int
    observation_id: int | None
    url: str
    source_url: str
    license_code: str
    license: str
    attribution: str
    commercial_use_allowed: bool


class INaturalistClient:
    def __init__(self, base_url: str, user_agent: str, timeout_seconds: float = 15.0, http: httpx.Client | None = None, sleep=time.sleep):
        self._http = http or httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout_seconds, headers={"User-Agent": user_agent})
        self._lock = threading.Lock()
        self._last_call = 0.0
        self._sleep = sleep

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            wait = _MIN_INTERVAL_SECONDS - (time.monotonic() - self._last_call)
            if wait > 0:
                self._sleep(wait)
            self._last_call = time.monotonic()
        try:
            response = self._http.get(path, params=params)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderUnavailableError("inaturalist", "iNaturalist request failed.") from exc

    def search_taxa(self, query: str, rank: str | None = None, per_page: int = 10) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"q": query, "per_page": per_page, "is_active": "true"}
        if rank:
            params["rank"] = rank
        return self._get("/taxa", params).get("results", [])

    def find_taxon_id(self, scientific_name: str, rank: str | None = None) -> int | None:
        for taxon in self.search_taxa(scientific_name, rank=rank, per_page=5):
            if taxon.get("name", "").lower() == scientific_name.lower():
                return taxon["id"]
        return None

    def observation_photos(self, taxon_id: int, taxon_name: str, *, per_page: int = 10) -> list[PhotoCandidate]:
        """Research-grade observation photos whose license allows commercial reuse."""
        data = self._get(
            "/observations",
            {
                "taxon_id": taxon_id,
                "quality_grade": "research",
                "photo_license": ",".join(sorted(COMMERCIAL_OK)),
                "photos": "true",
                "order_by": "votes",
                "per_page": per_page,
            },
        )
        candidates: list[PhotoCandidate] = []
        for observation in data.get("results", []):
            for photo in observation.get("photos", []):
                code = photo.get("license_code")
                if not commercial_use_allowed(code):
                    continue  # the filter applies per observation; re-check every photo
                url = (photo.get("url") or "").replace("/square.", "/medium.")
                if not url:
                    continue
                candidates.append(
                    PhotoCandidate(
                        taxon_name=taxon_name, photo_id=photo["id"], observation_id=observation.get("id"), url=url,
                        source_url=f"https://www.inaturalist.org/photos/{photo['id']}", license_code=code,
                        license=license_label(code), attribution=photo.get("attribution") or "", commercial_use_allowed=True,
                    )
                )
        return candidates
