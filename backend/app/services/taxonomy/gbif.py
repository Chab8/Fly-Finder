"""GBIF Species API client (no API key required).

Endpoints used (verified live 2026-10-31, docs: https://techdocs.gbif.org/en/openapi/):
  GET {base}/species/match?name=&rank=&kingdom=   name matching against the GBIF Backbone
  GET {base}/species/{key}                        a single name usage
  GET {base}/species/search?q=&rank=              full-text search (catalog tooling)
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

import httpx

from app.core.errors import ProviderUnavailableError
from app.schemas.identification import TaxonomyMatch

logger = logging.getLogger(__name__)
_CACHE_TTL_SECONDS = 24 * 3600
_CACHE_MAX = 5000


class GbifClient:
    def __init__(self, base_url: str, user_agent: str, timeout_seconds: float, http: httpx.Client | None = None):
        self._http = http or httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout_seconds, headers={"User-Agent": user_agent})
        self._cache: dict[tuple, tuple[float, TaxonomyMatch | None]] = {}
        self._lock = threading.Lock()

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        try:
            response = self._http.get(path, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise ProviderUnavailableError("gbif", "GBIF returned an error.", code="taxonomy_unavailable") from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderUnavailableError("gbif", "GBIF is unreachable.", code="taxonomy_unavailable") from exc

    @staticmethod
    def _to_match(data: dict[str, Any]) -> TaxonomyMatch | None:
        if not data or data.get("matchType") in (None, "NONE") or not data.get("usageKey"):
            return None
        key = data["usageKey"]
        return TaxonomyMatch(
            gbif_taxon_id=key,
            accepted_name=data.get("canonicalName") or data.get("scientificName"),
            rank=(data.get("rank") or "").lower() or None,
            status=data.get("status"),
            match_type=data.get("matchType"),
            kingdom=data.get("kingdom"), phylum=data.get("phylum"), class_name=data.get("class"),
            order=data.get("order"), family=data.get("family"), genus=data.get("genus"), species=data.get("species"),
            url=f"https://www.gbif.org/species/{key}",
        )

    def match(self, name: str, rank: str | None = None, kingdom: str | None = "Animalia") -> TaxonomyMatch | None:
        """Match a name to the GBIF Backbone. Returns None when GBIF has no match.

        A HIGHERRANK match means GBIF only recognised a broader taxon; callers should not
        treat that as confirmation of the specific name.
        """
        key = (name.strip().lower(), rank, kingdom)
        now = time.monotonic()
        with self._lock:
            cached = self._cache.get(key)
            if cached and now - cached[0] < _CACHE_TTL_SECONDS:
                return cached[1]
        params = {"name": name, "verbose": "false"}
        if rank:
            params["rank"] = rank.upper()
        if kingdom:
            params["kingdom"] = kingdom
        result = self._to_match(self._get("/species/match", params))
        with self._lock:
            if len(self._cache) >= _CACHE_MAX:
                self._cache.clear()
            self._cache[key] = (now, result)
        return result

    def get_species(self, key: int) -> dict[str, Any] | None:
        return self._get(f"/species/{key}")

    def search(self, query: str, rank: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"q": query, "limit": limit}
        if rank:
            params["rank"] = rank.upper()
        data = self._get("/species/search", params) or {}
        return data.get("results", [])
