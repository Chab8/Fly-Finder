"""Config validation, rate limiting, logging redaction, vector index and external API clients."""

import logging
import uuid

import httpx
import numpy as np
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.errors import ProviderUnavailableError, RateLimitedError
from app.core.logging import RedactingFilter
from app.core.rate_limit import SlidingWindowRateLimiter
from app.repositories.vector_index import InMemoryVectorIndex, VectorHit, aggregate_by_owner
from app.services.taxonomy.gbif import GbifClient
from app.services.taxonomy.inaturalist import INaturalistClient
from app.services.taxonomy.licenses import commercial_use_allowed


# ------------------------------------------------------------------ config
def test_production_requires_safe_settings():
    with pytest.raises(ValidationError, match="DEMO_MODE"):
        Settings(_env_file=None, environment="production", demo_mode=True)
    with pytest.raises(ValidationError, match="CATALOG_BACKEND"):
        Settings(_env_file=None, environment="production")
    with pytest.raises(ValidationError, match="CLIENT_HASH_SALT"):
        Settings(_env_file=None, environment="production", catalog_backend="postgres", database_url="postgresql://x")


def test_empty_env_values_mean_not_configured():
    settings = Settings(_env_file=None, gemini_api_key="", database_url="", cors_origins="https://a.com, https://b.com")
    assert settings.gemini_api_key is None and not settings.gemini_configured
    assert settings.cors_origins == ["https://a.com", "https://b.com"]


def test_secrets_are_not_printed():
    settings = Settings(_env_file=None, gemini_api_key="AIzaSecretValue123")
    assert "AIzaSecretValue123" not in repr(settings)


def test_log_redaction():
    record = logging.LogRecord("x", logging.INFO, "f", 1, "url %s", ("https://h/?key=AIzaSyA1234567890123456789012 postgresql://u:pw@db/x",), None)
    RedactingFilter().filter(record)
    assert "AIzaSy" not in record.msg and "pw@" not in record.msg


# ------------------------------------------------------------- rate limit
def test_rate_limiter_window():
    now = {"t": 0.0}
    limiter = SlidingWindowRateLimiter(2, 60, clock=lambda: now["t"])
    limiter.check("a")
    limiter.check("a")
    with pytest.raises(RateLimitedError):
        limiter.check("a")
    limiter.check("b")
    now["t"] = 61
    limiter.check("a")


# ------------------------------------------------------------ vector index
def test_in_memory_vector_index_roundtrip(tmp_path):
    owners = [uuid.uuid4(), uuid.uuid4()]
    vectors = np.array([[1, 0, 0], [0.9, 0.1, 0], [0, 1, 0]], dtype=np.float32)
    index = InMemoryVectorIndex("m1", [uuid.uuid4() for _ in range(3)], ["fly", "fly", "organism"], [owners[0], owners[0], owners[1]], vectors)
    path = tmp_path / "e.npz"
    index.save(path)
    loaded = InMemoryVectorIndex.from_file(path)
    hits = loaded.search("fly", np.array([1, 0, 0]), "m1")
    assert len(hits) == 1 and hits[0].owner_id == owners[0] and hits[0].similarity == pytest.approx(1.0)
    assert loaded.search("fly", np.array([1, 0, 0]), "other-model") == []  # never mix models
    assert loaded.search("organism", np.array([0, 1, 0]), "m1")[0].owner_id == owners[1]


def test_aggregate_keeps_best_image_per_owner():
    owner = uuid.uuid4()
    hits = [VectorHit(uuid.uuid4(), "fly", owner, 0.2), VectorHit(uuid.uuid4(), "fly", owner, 0.8)]
    assert [h.similarity for h in aggregate_by_owner(hits, 5)] == [0.8]


# -------------------------------------------------------------------- GBIF
def gbif_client(handler):
    return GbifClient("https://api.gbif.org/v1", "test", 1, http=httpx.Client(base_url="https://api.gbif.org/v1", transport=httpx.MockTransport(handler)))


def test_gbif_match_parsing_and_cache():
    calls = []

    def handler(request):
        calls.append(str(request.url))
        assert request.url.params["name"] == "Baetis" and request.url.params["rank"] == "GENUS"
        return httpx.Response(200, json={"usageKey": 1407108, "canonicalName": "Baetis", "rank": "GENUS", "status": "ACCEPTED",
                                         "matchType": "EXACT", "order": "Ephemeroptera", "family": "Baetidae", "class": "Insecta"})

    client = gbif_client(handler)
    match = client.match("Baetis", rank="genus")
    assert match.gbif_taxon_id == 1407108 and match.class_name == "Insecta" and match.url.endswith("/1407108")
    client.match("Baetis", rank="genus")
    assert len(calls) == 1


def test_gbif_no_match_and_outage():
    assert gbif_client(lambda r: httpx.Response(200, json={"matchType": "NONE"})).match("Nonexistus") is None
    with pytest.raises(ProviderUnavailableError):
        gbif_client(lambda r: httpx.Response(503)).match("Baetis")

    def broken(request):
        raise httpx.ConnectError("down")

    with pytest.raises(ProviderUnavailableError):
        gbif_client(broken).match("Baetis")


# ------------------------------------------------------------- iNaturalist
def test_inaturalist_only_returns_commercially_reusable_photos():
    def handler(request):
        assert request.url.params["photo_license"] == "cc-by,cc-by-sa,cc0"
        photo = lambda pid, lic: {"id": pid, "license_code": lic, "url": f"https://static.inaturalist.org/photos/{pid}/square.jpg", "attribution": "(c) someone"}  # noqa: E731
        return httpx.Response(200, json={"results": [{"id": 9, "photos": [photo(1, "cc-by"), photo(2, "cc-by-nc"), photo(3, None)]}]})

    sleeps = []
    client = INaturalistClient("https://api.inaturalist.org/v1", "test", http=httpx.Client(base_url="https://api.inaturalist.org/v1", transport=httpx.MockTransport(handler)), sleep=sleeps.append)
    photos = client.observation_photos(123, "Baetis")
    assert [p.photo_id for p in photos] == [1]
    assert photos[0].url.endswith("/medium.jpg") and photos[0].license == "CC BY 4.0"
    client.observation_photos(123, "Baetis")
    assert sleeps and sleeps[0] > 0  # throttled to 1 request/second


@pytest.mark.parametrize(("code", "ok"), [("cc0", True), ("CC-BY", True), ("cc-by-sa", True), ("cc-by-nc", False), ("cc-by-nd", False), (None, False)])
def test_license_policy(code, ok):
    assert commercial_use_allowed(code) is ok
