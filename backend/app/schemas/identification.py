"""API response shapes for the two identification engines.

Three different signals are kept strictly apart:
- ai_confidence:            the vision model's qualitative self-assessment (not a probability)
- visual_similarity:        cosine similarity between image embeddings (not a probability)
- biological_compatibility: documented organism <-> fly relationship from the catalog
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.models.catalog import Variant
from app.models.enums import (
    BiologicalCompatibility,
    FlyCategory,
    IdentificationKind,
    LifeStage,
    MatchType,
    TaxonRank,
)
from app.schemas.ai import AIConfidence, FlyFeatures, ImageQuality, SubjectType
from app.schemas.catalog import FlyPatternSummary, ImitatedOrganism, OrganismSummary
from app.schemas.commerce import ProductInfo


class MatchLevel(str, Enum):
    high_match = "high_match"
    moderate_match = "moderate_match"
    low_match = "low_match"
    inconclusive = "inconclusive"
    insufficient_image = "insufficient_image"
    not_compatible = "not_compatible"


class Notice(BaseModel):
    """A warning or limitation shown to the user. `code` is stable; `message` is localized."""

    code: str
    message: str


class EvidenceSource(BaseModel):
    name: str  # gemini | gbif | catalog | visual_similarity
    detail: str | None = None
    url: str | None = None


class AnalysisInfo(BaseModel):
    ai_provider: str | None
    ai_model: str | None
    ai_available: bool
    embedding_model: str | None
    embeddings_available: bool
    taxonomy_available: bool | None = None
    duration_ms: int
    is_demo: bool = False


class TaxonomyMatch(BaseModel):
    """Result of checking a name against the GBIF backbone taxonomy."""

    source: str = "gbif"
    gbif_taxon_id: int | None
    accepted_name: str | None
    rank: str | None
    status: str | None
    match_type: str | None
    kingdom: str | None = None
    phylum: str | None = None
    class_name: str | None = None
    order: str | None = None
    family: str | None = None
    genus: str | None = None
    species: str | None = None
    url: str | None = None


class OrganismCandidate(BaseModel):
    rank_position: int
    scientific_name: str
    taxonomic_rank: TaxonRank
    common_name: str | None
    order: str | None
    family: str | None
    genus: str | None
    ai_confidence: AIConfidence
    visual_evidence: str | None
    taxonomy: TaxonomyMatch | None
    taxonomy_verified: bool
    catalog_organism: OrganismSummary | None
    in_catalog: bool


class RecommendationTier(str, Enum):
    biological_same_stage = "biological_same_stage"
    biological_stage_unknown = "biological_stage_unknown"
    biological_other_stage = "biological_other_stage"
    visual_only = "visual_only"


class ScoreComponents(BaseModel):
    biological: float | None = None
    taxonomic_specificity: float | None = None
    life_stage: float | None = None
    imitation_type: float | None = None
    color: float | None = None
    visual: float | None = None


class FlyRecommendation(BaseModel):
    fly: FlyPatternSummary
    tier: RecommendationTier
    matched_organism: OrganismSummary | None
    life_stage: LifeStage | None
    match_type: MatchType | None
    biological_compatibility: BiologicalCompatibility | None
    expert_verified: bool
    visual_similarity: float | None = Field(description="Cosine similarity of image embeddings. Not a probability.")
    ranking_score: float = Field(description="Relative ordering score from an experimental heuristic. Not a probability.")
    components: ScoreComponents
    reasons: list[str]


class VisualFeatures(BaseModel):
    colors: list[str]
    morphological_features: list[str]
    estimated_length_mm: float | None
    size_reference: str | None
    habitat_hint: str | None


class SimilarCatalogOrganism(BaseModel):
    organism: OrganismSummary
    visual_similarity: float


class OrganismIdentificationResponse(BaseModel):
    identification_id: uuid.UUID | None
    kind: IdentificationKind = IdentificationKind.organism
    match_level: MatchLevel
    subject_type: SubjectType | None
    image_quality: ImageQuality | None
    primary: OrganismCandidate | None
    alternatives: list[OrganismCandidate]
    life_stage: LifeStage
    life_stage_confidence: AIConfidence
    visual_features: VisualFeatures | None
    recommendations: list[FlyRecommendation]
    visually_similar_organisms: list[SimilarCatalogOrganism]
    sources: list[EvidenceSource]
    warnings: list[Notice]
    analysis: AnalysisInfo


class FlyCandidate(BaseModel):
    rank_position: int
    pattern_name: str
    fly: FlyPatternSummary | None
    in_catalog: bool
    ai_confidence: AIConfidence | None
    name_match: str | None = Field(description="exact | alternate_name | fuzzy | none")
    visual_similarity: float | None = Field(description="Best cosine similarity against catalog images. Not a probability.")
    evidence: list[str]


class AIImitationHint(BaseModel):
    """Unverified suggestion from the vision model about what the fly imitates."""

    organism_group: str
    life_stage: LifeStage
    ai_confidence: AIConfidence
    catalog_organism: OrganismSummary | None


class FlyIdentificationResponse(BaseModel):
    identification_id: uuid.UUID | None
    kind: IdentificationKind = IdentificationKind.fly
    match_level: MatchLevel
    subject_type: SubjectType | None
    image_quality: ImageQuality | None
    primary: FlyCandidate | None
    alternatives: list[FlyCandidate]
    category: FlyCategory | None
    features: FlyFeatures | None
    is_attractor_likely: bool
    imitates: list[ImitatedOrganism]
    ai_imitation_hints: list[AIImitationHint]
    variants: list[Variant]
    products: list[ProductInfo]
    sources: list[EvidenceSource]
    warnings: list[Notice]
    analysis: AnalysisInfo


class IdentificationSummary(BaseModel):
    id: uuid.UUID
    kind: IdentificationKind
    created_at: datetime
    match_level: MatchLevel
    primary_label: str | None
    image_stored: bool
    is_demo: bool
