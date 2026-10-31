"""DEMO analyzer: deterministic, fictional output to exercise the app without an API key.

Every name it returns belongs to the fictional records in data/demo and every response
built from it is flagged is_demo=true. It performs no recognition at all.
"""

from __future__ import annotations

import numpy as np

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
from app.services.images.processing import ProcessedImage

_DARK_THRESHOLD = 25  # mean brightness (0-255) below which the demo reports an unusable image


def _is_dark(image: ProcessedImage) -> bool:
    return float(np.asarray(image.image.convert("L")).mean()) < _DARK_THRESHOLD


class DemoVisionAnalyzer:
    provider = "demo"
    model = "demo-fixed-responses"

    @property
    def available(self) -> bool:
        return True

    def analyze_organism(self, image: ProcessedImage, lang: str = "en") -> OrganismVisionResult:
        if _is_dark(image):
            return OrganismVisionResult(
                subject_type=SubjectType.no_clear_subject, image_quality=ImageQuality.unusable,
                image_quality_issues=["too dark (DEMO rule)"], cannot_identify_reason="DEMO: image too dark",
            )
        return OrganismVisionResult(
            subject_type=SubjectType.real_organism,
            image_quality=ImageQuality.good,
            candidates=[
                TaxonCandidate(
                    scientific_name="Demoensis ficticius", rank=TaxonRank.species, common_name_en="DEMO mayfly",
                    order="Demoptera", family="Demoidae", genus="Demoensis", confidence=AIConfidence.moderate,
                    visual_evidence="DEMO response: no real analysis was performed.",
                ),
                TaxonCandidate(
                    scientific_name="Demoidae", rank=TaxonRank.family, order="Demoptera", family="Demoidae",
                    confidence=AIConfidence.moderate, visual_evidence="DEMO response.",
                ),
            ],
            life_stage=LifeStage.nymph,
            life_stage_confidence=AIConfidence.moderate,
            colors=["olive", "brown"],
            morphological_features=["DEMO: three tails", "DEMO: gills on abdomen"],
        )

    def analyze_fly(self, image: ProcessedImage, known_patterns: list[str], lang: str = "en") -> FlyVisionResult:
        if _is_dark(image):
            return FlyVisionResult(
                subject_type=SubjectType.no_clear_subject, image_quality=ImageQuality.unusable,
                image_quality_issues=["too dark (DEMO rule)"], cannot_identify_reason="DEMO: image too dark",
            )
        return FlyVisionResult(
            subject_type=SubjectType.artificial_fly,
            image_quality=ImageQuality.good,
            category=FlyCategory.nymph,
            candidates=[
                FlyPatternCandidate(pattern_name="DEMO Nymph", confidence=AIConfidence.moderate, visual_evidence="DEMO response."),
                FlyPatternCandidate(pattern_name="DEMO Dun", confidence=AIConfidence.low, visual_evidence="DEMO response."),
            ],
            features=FlyFeatures(silhouette="DEMO: slim nymph", colors=["olive"], visible_materials=["DEMO: dubbing"]),
            imitation_hints=[ImitationHint(organism_group="Demoidae", life_stage=LifeStage.nymph, confidence=AIConfidence.moderate)],
        )
