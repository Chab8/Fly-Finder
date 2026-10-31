"""API <-> mobile contract.

The Flutter tests parse JSON fixtures in mobile/test/fixtures. This test regenerates those
responses from the real API code and fails if their structure drifted from the files.
Refresh the files with:  WRITE_FIXTURES=1 pytest tests/test_contract_fixtures.py
"""

import json
import os
import uuid

import pytest

from app.core.config import REPO_ROOT
from app.models.catalog import CatalogDataset, ProductPatternRecord, ProductRecord, StoreRecord, stable_id
from app.models.enums import FlyCategory, LifeStage, TaxonRank
from app.schemas.ai import (
    AIConfidence,
    FlyFeatures,
    FlyPatternCandidate,
    FlyVisionResult,
    ImageQuality,
    ImitationHint,
    OrganismVisionResult,
    SubjectType,
    TaxonCandidate,
)
from tests.conftest import FakeAnalyzer, FakeGbif, gbif_exact, make_image_bytes

FIXTURES = REPO_ROOT / "mobile" / "test" / "fixtures"
CLIENT = {"X-Client-Id": "00000000-0000-4000-8000-000000000001"}


def shape(value):
    """Structure of a JSON value: keys and element shapes, not the data."""
    if isinstance(value, dict):
        return {k: shape(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [shape(value[0])] if value else []
    return type(value).__name__ if value is not None else "null"


def check_or_write(name: str, payload) -> None:
    path = FIXTURES / name
    if os.environ.get("WRITE_FIXTURES") == "1":
        FIXTURES.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return
    if not path.exists():
        pytest.fail(f"{path} missing: run WRITE_FIXTURES=1 pytest {__file__}")
    stored = json.loads(path.read_text(encoding="utf-8"))
    assert shape(stored) == shape(payload), f"{name} no longer matches the API. Regenerate it and update the Flutter models."


@pytest.fixture
def commerce_dataset(catalog_dataset):
    fly = next(f for f in catalog_dataset.flies if f.slug == "woolly-bugger")
    store = StoreRecord(
        id=stable_id("store", "example-shop"), slug="example-shop", name="EXAMPLE Shop (fixture)", website="https://example.com",
        country="AR", currency="ARS", shipping_countries=("AR",), is_demo=True,
    )
    product = ProductRecord(
        id=stable_id("product", "example-shop", "1"), store_id=store.id, external_id="1", name="EXAMPLE Woolly Bugger #8",
        product_url="https://example.com/p/1", price="4500.00", currency="ARS", availability_status="in_stock",
        last_verified_at="2026-10-30T00:00:00+00:00", is_demo=True,
    )
    link = ProductPatternRecord(id=uuid.UUID(int=1), product_id=product.id, fly_pattern_id=fly.id, size="8")
    return catalog_dataset.merged(CatalogDataset(stores=[store], products=[product], product_patterns=[link])), fly.id


def test_contract_fixtures(client_for, commerce_dataset):
    dataset, fly_id = commerce_dataset
    organism_vision = OrganismVisionResult(
        subject_type=SubjectType.real_organism, image_quality=ImageQuality.good, life_stage=LifeStage.nymph,
        life_stage_confidence=AIConfidence.moderate, colors=["olive", "brown"], morphological_features=["two tails", "plate-like gills"],
        candidates=[
            TaxonCandidate(scientific_name="Baetis", rank=TaxonRank.genus, common_name_en="Blue-winged olive", order="Ephemeroptera",
                           family="Baetidae", genus="Baetis", confidence=AIConfidence.high, visual_evidence="Two tails, streamlined body"),
            TaxonCandidate(scientific_name="Heptageniidae", rank=TaxonRank.family, order="Ephemeroptera", family="Heptageniidae",
                           confidence=AIConfidence.low, visual_evidence="Somewhat flattened"),
        ],
    )
    fly_vision = FlyVisionResult(
        subject_type=SubjectType.artificial_fly, image_quality=ImageQuality.good, category=FlyCategory.streamer,
        features=FlyFeatures(silhouette="Long marabou tail", colors=["black"], visible_materials=["marabou", "chenille"]),
        candidates=[FlyPatternCandidate(pattern_name="Woolly Bugger", confidence=AIConfidence.high, visual_evidence="Marabou tail, palmered hackle")],
        imitation_hints=[ImitationHint(organism_group="Hirudinea", life_stage=LifeStage.adult, confidence=AIConfidence.moderate)],
    )
    gbif = FakeGbif({"baetis": gbif_exact("Baetis", "genus", order="Ephemeroptera", family="Baetidae", genus="Baetis", class_name="Insecta")})
    client = client_for(dataset=dataset, analyzer=FakeAnalyzer(organism=organism_vision, fly=fly_vision), gbif=gbif)

    files = {"image": ("p.jpg", make_image_bytes(), "image/jpeg")}
    organism = client.post("/api/v1/identify/organism", files=files, headers=CLIENT, params={"lang": "es"}).json()
    fly = client.post("/api/v1/identify/fly", files=files, headers=CLIENT, params={"lang": "es", "country": "AR"}).json()
    inconclusive_client = client_for(dataset=dataset, analyzer=FakeAnalyzer(organism=OrganismVisionResult(
        subject_type=SubjectType.artificial_fly, image_quality=ImageQuality.good)))
    not_compatible = inconclusive_client.post("/api/v1/identify/organism", files=files, headers=CLIENT).json()

    check_or_write("organism_result.json", organism)
    check_or_write("fly_result.json", fly)
    check_or_write("organism_not_compatible.json", not_compatible)
    check_or_write("fly_detail.json", client.get(f"/api/v1/flies/{fly_id}", params={"lang": "es"}).json())
    check_or_write("fly_products.json", client.get(f"/api/v1/flies/{fly_id}/products", params={"country": "AR"}).json())
    baetis = client.get("/api/v1/organisms", params={"q": "Baetis"}).json()
    check_or_write("organisms_page.json", baetis)
    check_or_write("organism_detail.json", client.get(f"/api/v1/organisms/{baetis['items'][0]['id']}", params={"lang": "es"}).json())
    check_or_write("history.json", client.get("/api/v1/identifications", headers=CLIENT).json())
