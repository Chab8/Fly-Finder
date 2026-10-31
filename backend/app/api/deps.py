"""Dependency wiring: builds every service once from Settings and exposes them to routes."""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from fastapi import Header, Query, Request

from app.catalog.csv_loader import load_catalog_dir
from app.core.config import CatalogBackend, Settings
from app.core.rate_limit import SlidingWindowRateLimiter
from app.models.catalog import CatalogDataset, ImageRecord
from app.repositories.catalog_snapshot import CatalogSnapshot, SnapshotProvider
from app.repositories.identification_store import IdentificationStore, InMemoryIdentificationStore
from app.repositories.vector_index import InMemoryVectorIndex, NullVectorIndex, VectorIndex
from app.services.ai.base import UnconfiguredVisionAnalyzer, VisionAnalyzer
from app.services.ai.demo import DemoVisionAnalyzer
from app.services.ai.gemini import GeminiVisionAnalyzer
from app.services.commerce.products import ProductService
from app.services.embeddings.base import DisabledEmbedder, ImageEmbedder
from app.services.embeddings.openclip import build_embedder
from app.services.i18n import normalize_language
from app.services.identification.common import PipelineDeps
from app.services.identification.fly import FlyIdentificationService
from app.services.identification.organism import OrganismIdentificationService
from app.services.recommendations.ranking import RecommendationEngine
from app.services.storage import SupabaseStorage
from app.services.taxonomy.gbif import GbifClient

logger = logging.getLogger(__name__)
_CLIENT_ID = re.compile(r"^[0-9a-fA-F-]{16,64}$")


@dataclass
class Container:
    settings: Settings
    snapshots: SnapshotProvider
    analyzer: VisionAnalyzer
    embedder: ImageEmbedder
    vector_index: VectorIndex
    identifications: IdentificationStore
    products: ProductService
    organism_service: OrganismIdentificationService
    fly_service: FlyIdentificationService
    rate_limiter: SlidingWindowRateLimiter
    resources: list[Any] = field(default_factory=list)  # closed on shutdown

    def close(self) -> None:
        for resource in self.resources:
            try:
                resource.close()
            except Exception:
                logger.exception("Error closing %s", type(resource).__name__)


def embeddings_file(settings: Settings) -> Any:
    slug = settings.embedding_model_id.replace(":", "__").replace("/", "_")
    return settings.catalog_dir / "embeddings" / f"{slug}.npz"


def image_url_resolver(settings: Settings):
    def resolve(image: ImageRecord) -> str | None:
        if image.storage_path and settings.supabase_url:
            base = settings.supabase_url.rstrip("/")
            return f"{base}/storage/v1/object/public/{settings.supabase_storage_bucket_catalog}/{image.storage_path}"
        return image.image_url

    return resolve


def load_csv_dataset(settings: Settings) -> CatalogDataset:
    result = load_catalog_dir(settings.catalog_dir)
    dataset = result.dataset
    if settings.demo_mode:
        demo = load_catalog_dir(settings.demo_dir)
        result.issues += demo.issues
        dataset = dataset.merged(demo.dataset)
    if result.errors:
        details = "\n".join(str(issue) for issue in result.errors[:20])
        raise RuntimeError(f"Catalog CSV has {len(result.errors)} errors. Run scripts/validate_dataset.py.\n{details}")
    return dataset


def build_analyzer(settings: Settings) -> VisionAnalyzer:
    if settings.demo_mode:
        return DemoVisionAnalyzer()
    if settings.gemini_api_key:
        return GeminiVisionAnalyzer(
            api_key=settings.gemini_api_key.get_secret_value(), model=settings.gemini_model,
            timeout_seconds=settings.gemini_timeout_seconds, thinking_level=settings.gemini_thinking_level,
        )
    return UnconfiguredVisionAnalyzer(settings.gemini_model)


def build_container(settings: Settings) -> Container:
    resolver = image_url_resolver(settings)
    resources: list[Any] = []

    if settings.catalog_backend == CatalogBackend.postgres:
        from app.repositories.postgres import PgCatalogLoader, PgIdentificationStore, PgVectorIndex, create_pool

        pool = create_pool(settings.database_url.get_secret_value())
        resources.append(pool)
        loader = PgCatalogLoader(pool)
        snapshots = SnapshotProvider(lambda: CatalogSnapshot(loader.load(), resolver), ttl_seconds=settings.catalog_refresh_seconds)
        vector_index: VectorIndex = PgVectorIndex(pool)
        identifications: IdentificationStore = PgIdentificationStore(pool)
    else:
        snapshots = SnapshotProvider(lambda: CatalogSnapshot(load_csv_dataset(settings), resolver))
        path = embeddings_file(settings)
        vector_index = InMemoryVectorIndex.from_file(path) if path.exists() else NullVectorIndex()
        identifications = InMemoryIdentificationStore()

    embedder: ImageEmbedder = (
        DisabledEmbedder(settings.embedding_model_id, "DEMO_MODE")
        if settings.demo_mode
        else build_embedder(
            settings.embeddings_enabled, settings.openclip_model, settings.openclip_pretrained,
            settings.openclip_device, settings.embedding_dimension,
        )
    )
    storage = None
    if settings.supabase_url and settings.supabase_service_role_key:
        storage = SupabaseStorage(settings.supabase_url, settings.supabase_service_role_key.get_secret_value())
    gbif = GbifClient(settings.gbif_api_url, settings.external_user_agent, settings.external_timeout_seconds)
    analyzer = build_analyzer(settings)

    deps = PipelineDeps(
        snapshots=snapshots, analyzer=analyzer, embedder=embedder, vector_index=vector_index,
        identifications=identifications, max_upload_bytes=settings.max_upload_bytes, demo_mode=settings.demo_mode,
        storage=storage, user_bucket=settings.supabase_storage_bucket_user,
        allow_user_image_storage=settings.allow_user_image_storage,
    )
    products = ProductService(snapshots)
    return Container(
        settings=settings, snapshots=snapshots, analyzer=analyzer, embedder=embedder, vector_index=vector_index,
        identifications=identifications, products=products,
        organism_service=OrganismIdentificationService(deps, gbif, RecommendationEngine()),
        fly_service=FlyIdentificationService(deps, products),
        rate_limiter=SlidingWindowRateLimiter(settings.identify_rate_limit_per_minute),
        resources=resources,
    )


# ------------------------------------------------------------ FastAPI dependencies
def get_container(request: Request) -> Container:
    return request.app.state.container


def get_language(lang: str | None = Query(None, description="en | es"), accept_language: str | None = Header(None)) -> str:
    return normalize_language(lang or accept_language)


def get_client_hash(request: Request, x_client_id: str | None = Header(None)) -> str | None:
    """Anonymous install id generated on the device. Only its salted hash is ever stored."""
    if not x_client_id or not _CLIENT_ID.match(x_client_id):
        return None
    salt = request.app.state.container.settings.client_hash_salt.get_secret_value()
    return hashlib.sha256(f"{salt}:{x_client_id}".encode()).hexdigest()
