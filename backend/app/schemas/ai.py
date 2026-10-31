"""Structured-output contracts requested from the vision model.

The model must answer with JSON that validates against these schemas; anything else is
rejected. Every schema lets the model say it cannot identify the subject.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from app.models.enums import FlyCategory, LifeStage, TaxonRank


class SubjectType(str, Enum):
    real_organism = "real_organism"
    artificial_fly = "artificial_fly"
    both = "both"
    other = "other"
    no_clear_subject = "no_clear_subject"


class ImageQuality(str, Enum):
    good = "good"
    acceptable = "acceptable"
    poor = "poor"
    unusable = "unusable"


class AIConfidence(str, Enum):
    """The model's own qualitative confidence. Not a calibrated probability."""

    high = "high"
    moderate = "moderate"
    low = "low"
    none = "none"


class TaxonCandidate(BaseModel):
    scientific_name: str = Field(description="Scientific name at the most specific rank the image justifies. Never invent a species.")
    rank: TaxonRank = Field(description="Taxonomic rank of scientific_name.")
    common_name_en: str | None = Field(default=None, description="English common name if widely used, else null.")
    order: str | None = None
    family: str | None = None
    genus: str | None = None
    confidence: AIConfidence
    visual_evidence: str = Field(description="Short list of visible features supporting this candidate.")


class OrganismVisionResult(BaseModel):
    subject_type: SubjectType
    image_quality: ImageQuality
    image_quality_issues: list[str] = Field(default_factory=list, description="e.g. blurry, too dark, subject too small, occluded.")
    candidates: list[TaxonCandidate] = Field(default_factory=list, max_length=5, description="Ordered best first. Empty if no defensible identification.")
    life_stage: LifeStage = LifeStage.unknown
    life_stage_confidence: AIConfidence = AIConfidence.none
    estimated_length_mm: float | None = Field(default=None, ge=0, description="Only if a scale reference is visible; otherwise null.")
    size_reference: str | None = Field(default=None, description="The visible object used to estimate size, if any.")
    colors: list[str] = Field(default_factory=list)
    morphological_features: list[str] = Field(default_factory=list)
    habitat_hint: str | None = None
    cannot_identify_reason: str | None = None


class FlyFeatures(BaseModel):
    silhouette: str | None = None
    colors: list[str] = Field(default_factory=list)
    visible_materials: list[str] = Field(default_factory=list)
    has_wing: bool | None = None
    wing_description: str | None = None
    has_tail: bool | None = None
    has_bead_head: bool | None = None
    hackle_description: str | None = None
    body_description: str | None = None


class FlyPatternCandidate(BaseModel):
    pattern_name: str = Field(description="Common name of the tying pattern.")
    confidence: AIConfidence
    visual_evidence: str


class ImitationHint(BaseModel):
    organism_group: str = Field(description="Taxon or group the fly appears to imitate, e.g. 'Ephemeroptera', 'Baitfish', 'Decapoda'.")
    life_stage: LifeStage = LifeStage.unknown
    confidence: AIConfidence


class FlyVisionResult(BaseModel):
    subject_type: SubjectType
    image_quality: ImageQuality
    image_quality_issues: list[str] = Field(default_factory=list)
    category: FlyCategory | None = None
    candidates: list[FlyPatternCandidate] = Field(default_factory=list, max_length=5, description="Ordered best first. Empty if not recognizable.")
    features: FlyFeatures = Field(default_factory=FlyFeatures)
    is_attractor_likely: bool = Field(default=False, description="True if the fly does not imitate a specific organism.")
    imitation_hints: list[ImitationHint] = Field(default_factory=list, max_length=4)
    cannot_identify_reason: str | None = None
