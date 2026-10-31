"""Vision analyzer interface. Identification services depend on this, never on a vendor SDK."""

from __future__ import annotations

from typing import Protocol

from app.core.errors import ProviderUnavailableError
from app.schemas.ai import FlyVisionResult, OrganismVisionResult
from app.services.images.processing import ProcessedImage


class VisionAnalyzer(Protocol):
    provider: str
    model: str | None

    @property
    def available(self) -> bool: ...

    def analyze_organism(self, image: ProcessedImage, lang: str = "en") -> OrganismVisionResult: ...

    def analyze_fly(self, image: ProcessedImage, known_patterns: list[str], lang: str = "en") -> FlyVisionResult: ...


class UnconfiguredVisionAnalyzer:
    """Placeholder used until GEMINI_API_KEY is set. Every call reports the provider as unavailable."""

    provider = "gemini"

    def __init__(self, model: str | None):
        self.model = model

    @property
    def available(self) -> bool:
        return False

    def _fail(self):
        raise ProviderUnavailableError("gemini", "AI analysis is not configured on the server.", code="ai_not_configured")

    def analyze_organism(self, image: ProcessedImage, lang: str = "en") -> OrganismVisionResult:
        self._fail()

    def analyze_fly(self, image: ProcessedImage, known_patterns: list[str], lang: str = "en") -> FlyVisionResult:
        self._fail()
