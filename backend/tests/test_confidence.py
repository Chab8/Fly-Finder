import pytest

from app.schemas.ai import AIConfidence, ImageQuality, SubjectType
from app.schemas.identification import MatchLevel
from app.services.identification.confidence import fly_level, gate_subject, organism_level, visual_only_level

Q = ImageQuality


@pytest.mark.parametrize(
    ("subject", "quality", "expected"),
    [
        (SubjectType.real_organism, Q.good, None),
        (SubjectType.both, Q.good, None),
        (SubjectType.artificial_fly, Q.good, MatchLevel.not_compatible),
        (SubjectType.other, Q.acceptable, MatchLevel.not_compatible),
        (SubjectType.no_clear_subject, Q.acceptable, MatchLevel.inconclusive),
        (SubjectType.real_organism, Q.unusable, MatchLevel.insufficient_image),
    ],
)
def test_gate_subject(subject, quality, expected):
    assert gate_subject(subject, quality, SubjectType.real_organism) == expected


def test_organism_level_downgrades_on_gbif_rejection_and_poor_quality():
    assert organism_level(AIConfidence.high, quality=Q.good, name_rejected_by_gbif=False) == MatchLevel.high_match
    assert organism_level(AIConfidence.high, quality=Q.good, name_rejected_by_gbif=True) == MatchLevel.moderate_match
    assert organism_level(AIConfidence.high, quality=Q.poor, name_rejected_by_gbif=True) == MatchLevel.low_match
    assert organism_level(AIConfidence.low, quality=Q.poor, name_rejected_by_gbif=True) == MatchLevel.low_match
    assert organism_level(AIConfidence.none, quality=Q.good, name_rejected_by_gbif=False) == MatchLevel.inconclusive


def test_fly_level_downgrades_outside_catalog():
    assert fly_level(AIConfidence.high, quality=Q.good, in_catalog=True, fuzzy_name=False) == MatchLevel.high_match
    assert fly_level(AIConfidence.high, quality=Q.good, in_catalog=False, fuzzy_name=False) == MatchLevel.moderate_match
    assert fly_level(AIConfidence.moderate, quality=Q.good, in_catalog=True, fuzzy_name=True) == MatchLevel.low_match


def test_visual_alone_is_never_more_than_low():
    assert visual_only_level(0.99, 0.85) == MatchLevel.low_match
    assert visual_only_level(0.5, 0.85) == MatchLevel.inconclusive
    assert visual_only_level(None, 0.85) == MatchLevel.inconclusive
