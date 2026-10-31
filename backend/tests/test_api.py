"""Endpoint tests through FastAPI's TestClient with faked providers."""

import uuid

import pytest

from app.core.config import Settings
from app.models.catalog import CatalogDataset, ProductPatternRecord, ProductRecord, StoreRecord, stable_id
from app.schemas.ai import AIConfidence, FlyPatternCandidate, FlyVisionResult, ImageQuality, SubjectType
from tests.conftest import FakeAnalyzer, FakeEmbedder, make_image_bytes

CLIENT_ID = str(uuid.uuid4())


def upload(client, path="/api/v1/identify/organism", data=None, name="photo.jpg", headers=None, **params):
    return client.post(path, files={"image": (name, data or make_image_bytes(), "image/jpeg")}, params=params, headers=headers or {})


def test_health_and_ready(client_for):
    client = client_for()
    assert client.get("/api/v1/health").json() == {"status": "ok"}
    ready = client.get("/api/v1/ready").json()
    assert ready["status"] == "ready"
    assert ready["components"]["catalog"]["organisms"] >= 30
    assert ready["components"]["ai"]["status"] == "not_configured"


def test_catalog_endpoints(client_for):
    client = client_for()
    organisms = client.get("/api/v1/organisms", params={"q": "baetis"}).json()
    assert organisms["total"] >= 1
    detail = client.get(f"/api/v1/organisms/{organisms['items'][0]['id']}", params={"lang": "es"}).json()
    assert detail["scientific_name"] == "Baetis" and detail["text_language"] == "es"
    flies = client.get("/api/v1/flies", params={"category": "saltwater"}).json()
    assert flies["total"] >= 5
    fly = client.get(f"/api/v1/flies/{flies['items'][0]['id']}").json()
    assert "materials" in fly and "imitates" in fly
    search = client.get("/api/v1/search", params={"q": "caddis"}).json()
    assert search["flies"] and search["organisms"]


def test_accept_language_header_is_used(client_for):
    client = client_for()
    items = client.get("/api/v1/organisms", params={"q": "Plecoptera"}, headers={"Accept-Language": "es-AR,es;q=0.9"}).json()["items"]
    assert items[0]["common_name"] == "Plecópteros"


def test_not_found_and_validation_errors_have_consistent_shape(client_for):
    client = client_for()
    missing = client.get(f"/api/v1/flies/{uuid.uuid4()}")
    assert missing.status_code == 404 and missing.json()["error"]["code"] == "not_found"
    bad = client.get("/api/v1/flies/not-a-uuid")
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "validation_error"
    assert client.get("/api/v1/search", params={"q": "x"}).status_code == 422


def test_identify_organism_endpoint_without_ai_but_with_embeddings(client_for):
    response = upload(client_for(), headers={"X-Client-Id": CLIENT_ID})
    assert response.status_code == 200
    body = response.json()
    assert body["match_level"] == "inconclusive"
    assert {w["code"] for w in body["warnings"]} >= {"ai_unavailable"}


def test_identify_fly_endpoint(client_for):
    vision = FlyVisionResult(
        subject_type=SubjectType.artificial_fly, image_quality=ImageQuality.good,
        candidates=[FlyPatternCandidate(pattern_name="Woolly Bugger", confidence=AIConfidence.moderate, visual_evidence="marabou")],
    )
    client = client_for(analyzer=FakeAnalyzer(fly=vision))
    body = upload(client, "/api/v1/identify/fly", headers={"X-Client-Id": CLIENT_ID}, lang="es", country="ar").json()
    assert body["match_level"] == "moderate_match" and body["primary"]["fly"]["slug"] == "woolly-bugger"
    assert body["imitates"]
    history = client.get("/api/v1/identifications", headers={"X-Client-Id": CLIENT_ID}).json()
    assert history[0]["kind"] == "fly" and history[0]["primary_label"] == "Woolly Bugger" and history[0]["image_stored"] is False
    stored = client.get(f"/api/v1/identifications/{history[0]['id']}", headers={"X-Client-Id": CLIENT_ID}).json()
    assert stored["primary"]["pattern_name"] == "Woolly Bugger"


def test_history_is_private_per_client(client_for):
    client = client_for()
    upload(client, headers={"X-Client-Id": CLIENT_ID})
    assert client.get("/api/v1/identifications", headers={"X-Client-Id": str(uuid.uuid4())}).json() == []
    assert client.get("/api/v1/identifications").status_code == 400


def test_invalid_file_type(client_for):
    response = upload(client_for(), data=b"hello world" * 100, name="photo.jpg")
    assert response.status_code == 422 and response.json()["error"]["code"] == "unreadable_image"


def test_missing_file(client_for):
    assert client_for().post("/api/v1/identify/organism").status_code == 422


def test_upload_size_limit(client_for):
    client = client_for(settings=Settings(_env_file=None, max_upload_mb=1))
    response = upload(client, data=make_image_bytes("PNG", size=(1200, 1200)))
    assert response.status_code == 413 and response.json()["error"]["code"] == "image_too_large"


def test_rate_limit(client_for):
    client = client_for(rate_limit=2)
    assert [upload(client, headers={"X-Client-Id": CLIENT_ID}).status_code for _ in range(3)] == [200, 200, 429]
    assert upload(client, headers={"X-Client-Id": CLIENT_ID}).json()["error"]["details"]["retry_after_seconds"] > 0


def test_everything_down_returns_503(client_for):
    client = client_for(analyzer=FakeAnalyzer(available=False), embedder=FakeEmbedder(available=False))
    response = upload(client)
    assert response.status_code == 503 and response.json()["error"]["code"] == "analysis_unavailable"


@pytest.fixture
def commerce_dataset(catalog_dataset):
    fly = next(f for f in catalog_dataset.flies if f.slug == "adams")
    store_ar = StoreRecord(id=stable_id("store", "a"), slug="a", name="Shop A", website="https://a.example.com", country="AR", currency="ARS", shipping_countries=("AR",))
    store_us = StoreRecord(id=stable_id("store", "b"), slug="b", name="Shop B", website="https://b.example.com", country="US", currency="USD", shipping_countries=("WORLDWIDE",))
    products = [
        ProductRecord(id=stable_id("product", "a", "1"), store_id=store_ar.id, external_id="1", name="Adams #14", product_url="https://a.example.com/1",
                      price="4500.00", currency="ARS", availability_status="in_stock", last_verified_at="2026-10-30T00:00:00+00:00"),
        ProductRecord(id=stable_id("product", "b", "2"), store_id=store_us.id, external_id="2", name="Adams #16", product_url="https://b.example.com/2",
                      affiliate_url="https://b.example.com/2?ref=ff", availability_status="unknown"),
    ]
    links = [ProductPatternRecord(id=uuid.uuid4(), product_id=p.id, fly_pattern_id=fly.id, size=s) for p, s in zip(products, ["14", "16"], strict=True)]
    return catalog_dataset.merged(CatalogDataset(stores=[store_ar, store_us], products=products, product_patterns=links)), fly.id


def test_products_keep_currency_and_never_invent_prices(client_for, commerce_dataset):
    dataset, adams_id = commerce_dataset
    client = client_for(dataset=dataset)
    products = client.get(f"/api/v1/flies/{adams_id}/products", params={"country": "CL"}).json()
    assert [p["name"] for p in products] == ["Adams #16", "Adams #14"]  # only Shop B ships to CL
    assert products[0]["price"] is None and products[0]["currency"] is None
    assert products[0]["buy_url"].endswith("?ref=ff")  # affiliate link preferred
    assert products[1]["price"] == "4500.00" and products[1]["currency"] == "ARS"
    assert products[1]["ships_to_requested_country"] is False
    stores = client.get("/api/v1/stores", params={"country": "CL"}).json()
    assert [s["slug"] for s in stores] == ["b"]
    page = client.get("/api/v1/products", params={"fly_id": str(adams_id)}).json()
    assert page["total"] == 2
    assert client.get(f"/api/v1/flies/{adams_id}").json()["product_count"] == 2


def test_empty_products_for_pattern_without_offers(client_for, snapshot):
    fly = next(f for f in snapshot.flies.values() if f.slug == "zebra-midge")
    assert client_for().get(f"/api/v1/flies/{fly.id}/products").json() == []
