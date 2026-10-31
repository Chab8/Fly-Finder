"""Pipeline steps shared by the organism and fly identification services."""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import numpy as np

from app.core.errors import ProviderResponseError, ProviderUnavailableError
from app.repositories.catalog_snapshot import SnapshotProvider
from app.repositories.identification_store import CandidateRow, IdentificationRecord, IdentificationStore
from app.repositories.vector_index import VectorIndex
from app.schemas.identification import AnalysisInfo, Notice
from app.services.ai.base import VisionAnalyzer
from app.services.embeddings.base import ImageEmbedder
from app.services.i18n import t
from app.services.images.processing import ProcessedImage, process_image
from app.services.storage import SupabaseStorage

logger = logging.getLogger(__name__)


@dataclass
class IdentificationContext:
    lang: str
    client_hash: str | None
    store_image: bool = False
    started: float = field(default_factory=time.monotonic)
    warnings: list[Notice] = field(default_factory=list)
    ai_available: bool = False
    embeddings_available: bool = False

    def warn(self, code: str, **params: object) -> None:
        if not any(w.code == code for w in self.warnings):
            self.warnings.append(Notice(code=code, message=t(code, self.lang, **params)))

    def elapsed_ms(self) -> int:
        return int((time.monotonic() - self.started) * 1000)


@dataclass
class PipelineDeps:
    snapshots: SnapshotProvider
    analyzer: VisionAnalyzer
    embedder: ImageEmbedder
    vector_index: VectorIndex
    identifications: IdentificationStore
    max_upload_bytes: int
    demo_mode: bool = False
    storage: SupabaseStorage | None = None
    user_bucket: str = "user-uploads"
    allow_user_image_storage: bool = False


class IdentificationPipeline:
    """Base class: image preparation, guarded provider calls and logging."""

    kind: str

    def __init__(self, deps: PipelineDeps):
        self.deps = deps

    def prepare(self, data: bytes, ctx: IdentificationContext) -> ProcessedImage:
        image = process_image(data, max_bytes=self.deps.max_upload_bytes)
        for code in image.warnings:
            ctx.warn(code)
        if self.deps.demo_mode:
            ctx.warn("demo_mode")
        return image

    def run_ai(self, call, ctx: IdentificationContext) -> Any | None:
        """Call the vision model; on failure return None and record why (never crash the request)."""
        if not self.deps.analyzer.available:
            ctx.warn("ai_unavailable")
            return None
        try:
            result = call()
            ctx.ai_available = True
            return result
        except ProviderUnavailableError as exc:
            logger.warning("AI unavailable for %s identification: %s", self.kind, exc.code)
            ctx.warn("ai_unavailable")
        except ProviderResponseError:
            ctx.warn("ai_bad_response")
        return None

    def embed(self, image: ProcessedImage, ctx: IdentificationContext) -> np.ndarray | None:
        if not self.deps.embedder.available:
            ctx.warn("embeddings_unavailable")
            return None
        try:
            vector = self.deps.embedder.embed(image.image)
            ctx.embeddings_available = True
            return vector
        except Exception:  # model load or inference failure must not break identification
            logger.exception("Embedding failed")
            ctx.warn("embeddings_unavailable")
            return None

    def similar(self, owner_kind: str, vector: np.ndarray | None, k: int):
        if vector is None:
            return []
        try:
            return self.deps.vector_index.search(owner_kind, vector, self.deps.embedder.model_id, k)
        except Exception:
            logger.exception("Vector search failed")
            return []

    def analysis_info(self, ctx: IdentificationContext) -> AnalysisInfo:
        analyzer = self.deps.analyzer
        return AnalysisInfo(
            ai_provider=analyzer.provider, ai_model=analyzer.model, ai_available=ctx.ai_available,
            embedding_model=self.deps.embedder.model_id if ctx.embeddings_available else None,
            embeddings_available=ctx.embeddings_available, duration_ms=ctx.elapsed_ms(), is_demo=self.deps.demo_mode,
        )

    def maybe_store_image(self, image: ProcessedImage, ctx: IdentificationContext, identification_id: uuid.UUID) -> str | None:
        """Store the user's photo only if the product setting allows it AND the user consented."""
        if not ctx.store_image:
            return None
        if not (self.deps.allow_user_image_storage and self.deps.storage):
            ctx.warn("image_storage_skipped")
            return None
        path = f"{self.kind}/{datetime.now(UTC):%Y/%m}/{identification_id}.jpg"
        try:
            return self.deps.storage.upload(self.deps.user_bucket, path, image.jpeg_bytes, "image/jpeg")
        except ProviderUnavailableError:
            ctx.warn("image_storage_skipped")
            return None

    def log(
        self, ctx: IdentificationContext, image: ProcessedImage, response: Any, primary_label: str | None,
        candidates: list[CandidateRow],
    ) -> uuid.UUID | None:
        identification_id = uuid.uuid4()
        storage_path = self.maybe_store_image(image, ctx, identification_id)
        sources = []
        if ctx.ai_available:
            sources.append(self.deps.analyzer.provider)
        if ctx.embeddings_available:
            sources.append("open_clip")
        record = IdentificationRecord(
            id=identification_id, client_hash=ctx.client_hash, kind=self.kind, match_level=response.match_level.value,
            primary_label=primary_label, result=response.model_dump(mode="json", exclude={"identification_id"}),
            analysis_source="+".join(sources) or "none", ai_model=self.deps.analyzer.model if ctx.ai_available else None,
            embedding_model=self.deps.embedder.model_id if ctx.embeddings_available else None,
            image_consent=ctx.store_image, image_storage_path=storage_path, is_demo=self.deps.demo_mode,
            created_at=datetime.now(UTC), candidates=candidates,
        )
        try:
            self.deps.identifications.save(record)
            return identification_id
        except Exception:
            logger.exception("Could not log identification")
            return None
