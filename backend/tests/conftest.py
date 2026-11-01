"""Shared fixtures. No test calls Gemini, GBIF or iNaturalist: they are all faked here."""

from __future__ import annotations

import io
import uuid
from collections.abc import Callable

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.api.deps import Container, load_csv_dataset
from app.core.config import REPO_ROOT, Settings
from app.core.errors import ProviderUnavailableError
from app.core.rate_limit import SlidingWindowRateLimiter
from app.main import create_app
from app.repositories.catalog_snapshot import CatalogSnapshot, SnapshotProvider
from app.repositories.identification_store import InMemoryIdentificationStore
from app.repositories.vector_index import VectorHit
from app.schemas.ai import FlyVisionResult, OrganismVisionResult
from app.schemas.identification import TaxonomyMatch
from app.services.commerce.products import ProductService
from app.services.identification.common import PipelineDeps
from app.services.identification.fly import FlyIdentificationService
from app.services.identification.organism import OrganismIdentificationService
from app.services.recommendations.ranking import RecommendationEngine


# ------------------------------------------------------------------ images
def make_image_bytes(fmt: str = "JPEG", size: tuple[int, int] = (800, 600), *, dark: bool = False, flat: bool = False, mode: str = "RGB") -> bytes:
    rng = np.random.default_rng(42)
    if flat:
        array = np.full((size[1], size[0], 3), 128, dtype=np.uint8)
    else:
        array = rng.integers(0, 255, (size[1], size[0], 3), dtype=np.uint8)
    if dark:
        array = (array // 20).astype(np.uint8)
    image = Image.fromarray(array, "RGB").convert(mode)
    buffer = io.BytesIO()
    image.save(buffer, format=fmt)
    return buffer.getvalue()


@pytest.fixture
def jpeg_bytes() -> bytes:
    return make_image_bytes()


# ------------------------------------------------------------------ fakes
class FakeAnalyzer:
    provider = "fake"
    model = "fake-vision-1"

    def __init__(self, organism: OrganismVisionResult | None = None, fly: FlyVisionResult | None = None, error: Exception | None = None, available: bool = True):
        self.organism, self.fly, self.error, self._available = organism, fly, error, available
        self.calls: list[tuple[str, object]] = []

    @property
    def available(self) -> bool:
        return self._available

    def analyze_organism(self, image, lang="en", known_taxa=None):
        self.calls.append(("organism", known_taxa))
        if self.error:
            raise self.error
        return self.organism

    def analyze_fly(self, image, known_patterns, lang="en", pattern_profiles=None):
        self.calls.append(("fly", known_patterns))
        self.fly_profiles = pattern_profiles
        if self.error:
            raise self.error
        return self.fly


class FakeEmbedder:
    model_id = "fake:clip"

    def __init__(self, available: bool = True, fail: bool = False):
        self._available, self._fail = available, fail

    @property
    def available(self) -> bool:
        return self._available

    def embed(self, image):
        if self._fail:
            raise RuntimeError("boom")
        vector = np.ones(8, dtype=np.float32)
        return vector / np.linalg.norm(vector)


class FakeVectorIndex:
    def __init__(self, hits: dict[str, list[VectorHit]] | None = None):
        self.hits = hits or {}

    def search(self, owner_kind, embedding, model, k=10):
        return self.hits.get(owner_kind, [])[:k]


class FakeGbif:
    """Returns EXACT matches for names in `known`, None for others, or raises when `down`."""

    def __init__(self, known: dict[str, TaxonomyMatch] | None = None, down: bool = False):
        self.known = known or {}
        self.down = down
        self.calls: list[str] = []

    def match(self, name, rank=None, kingdom="Animalia"):
        self.calls.append(name)
        if self.down:
            raise ProviderUnavailableError("gbif", "down", code="taxonomy_unavailable")
        return self.known.get(name.lower())


def gbif_exact(name: str, rank: str, **taxonomy) -> TaxonomyMatch:
    return TaxonomyMatch(gbif_taxon_id=1, accepted_name=name, rank=rank, status="ACCEPTED", match_type="EXACT", **taxonomy)


# ------------------------------------------------------------------ container
@pytest.fixture(scope="session")
def catalog_dataset():
    settings = Settings(_env_file=None)
    return load_csv_dataset(settings)


@pytest.fixture
def snapshot(catalog_dataset) -> CatalogSnapshot:
    return CatalogSnapshot(catalog_dataset, lambda image: image.image_url)


def fly_id(snapshot: CatalogSnapshot, slug: str) -> uuid.UUID:
    return next(f.id for f in snapshot.flies.values() if f.slug == slug)


def organism_id(snapshot: CatalogSnapshot, name: str) -> uuid.UUID:
    return snapshot.find_organism_by_name(name).id


@pytest.fixture
def make_container(catalog_dataset) -> Callable[..., Container]:
    def factory(
        *, analyzer=None, embedder=None, vector_index=None, gbif=None, dataset=None, settings: Settings | None = None,
        rate_limit: int = 1000, demo_mode: bool = False,
    ) -> Container:
        settings = settings or Settings(_env_file=None, identify_rate_limit_per_minute=rate_limit, demo_mode=demo_mode)
        data = dataset or catalog_dataset
        snapshots = SnapshotProvider(lambda: CatalogSnapshot(data, lambda image: image.image_url))
        analyzer = analyzer or FakeAnalyzer(available=False)
        embedder = embedder or FakeEmbedder()
        vector_index = vector_index or FakeVectorIndex()
        store = InMemoryIdentificationStore()
        deps = PipelineDeps(
            snapshots=snapshots, analyzer=analyzer, embedder=embedder, vector_index=vector_index, identifications=store,
            max_upload_bytes=settings.max_upload_bytes, demo_mode=demo_mode,
        )
        products = ProductService(snapshots)
        return Container(
            settings=settings, snapshots=snapshots, analyzer=analyzer, embedder=embedder, vector_index=vector_index,
            identifications=store, products=products,
            organism_service=OrganismIdentificationService(deps, gbif if gbif is not None else FakeGbif(), RecommendationEngine()),
            fly_service=FlyIdentificationService(deps, products),
            rate_limiter=SlidingWindowRateLimiter(settings.identify_rate_limit_per_minute),
        )

    return factory


@pytest.fixture
def client_for(make_container) -> Callable[..., TestClient]:
    clients = []

    def factory(**kwargs) -> TestClient:
        container = kwargs.pop("container", None) or make_container(**kwargs)
        client = TestClient(create_app(container=container))
        client.__enter__()
        clients.append(client)
        return client

    yield factory
    for client in clients:
        client.__exit__(None, None, None)


DEMO_DIR = REPO_ROOT / "data" / "demo"
TEMPLATES_DIR = REPO_ROOT / "data" / "import_templates"
CATALOG_DIR = REPO_ROOT / "data" / "catalog"
