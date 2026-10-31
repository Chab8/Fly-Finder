"""Rules that turn evidence into a qualitative MatchLevel.

There is no numeric "confidence %": the level is derived from explicit, documented rules
(docs/AI_PIPELINE.md#match-levels) so every result can be explained.
"""

from __future__ import annotations

from app.schemas.ai import AIConfidence, ImageQuality, SubjectType
from app.schemas.identification import MatchLevel

_LEVEL_FROM_AI = {
    AIConfidence.high: MatchLevel.high_match,
    AIConfidence.moderate: MatchLevel.moderate_match,
    AIConfidence.low: MatchLevel.low_match,
}
_DOWNGRADE = {
    MatchLevel.high_match: MatchLevel.moderate_match,
    MatchLevel.moderate_match: MatchLevel.low_match,
    MatchLevel.low_match: MatchLevel.low_match,
}


def downgrade(level: MatchLevel, steps: int = 1) -> MatchLevel:
    for _ in range(steps):
        level = _DOWNGRADE.get(level, level)
    return level


def gate_subject(subject: SubjectType, quality: ImageQuality, expected: SubjectType) -> MatchLevel | None:
    """Return a terminal level if the image cannot be analysed for this function."""
    if quality == ImageQuality.unusable:
        return MatchLevel.insufficient_image
    if subject in (expected, SubjectType.both):
        return None
    if subject == SubjectType.no_clear_subject:
        return MatchLevel.inconclusive
    return MatchLevel.not_compatible


def organism_level(ai_confidence: AIConfidence | None, *, quality: ImageQuality, name_rejected_by_gbif: bool) -> MatchLevel:
    if ai_confidence is None or ai_confidence == AIConfidence.none:
        return MatchLevel.inconclusive
    level = _LEVEL_FROM_AI[ai_confidence]
    steps = int(name_rejected_by_gbif) + int(quality == ImageQuality.poor)
    return downgrade(level, steps)


def fly_level(ai_confidence: AIConfidence | None, *, quality: ImageQuality, in_catalog: bool, fuzzy_name: bool) -> MatchLevel:
    if ai_confidence is None or ai_confidence == AIConfidence.none:
        return MatchLevel.inconclusive
    level = _LEVEL_FROM_AI[ai_confidence]
    steps = int(not in_catalog) + int(fuzzy_name) + int(quality == ImageQuality.poor)
    return downgrade(level, steps)


def visual_only_level(best_similarity: float | None, strong_threshold: float) -> MatchLevel:
    """Without the AI, visual similarity alone can at most suggest a low match."""
    if best_similarity is not None and best_similarity >= strong_threshold:
        return MatchLevel.low_match
    return MatchLevel.inconclusive
