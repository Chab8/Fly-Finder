import uuid

import pytest

from app.core.errors import ProviderResponseError, ProviderUnavailableError
from app.models.enums import FlyCategory, LifeStage, TaxonRank
from app.repositories.vector_index import VectorHit
from app.schemas.ai import (
    AIConfidence,
    FlyPatternCandidate,
    FlyVisionResult,
    ImageQuality,
    ImitationHint,
    OrganismVisionResult,
    SubjectType,
    TaxonCandidate,
)
from app.schemas.identification import MatchLevel, RecommendationTier
from app.services.identification.common import IdentificationContext
from tests.conftest import FakeAnalyzer, FakeEmbedder, FakeGbif, FakeVectorIndex, fly_id, gbif_exact, make_image_bytes, organism_id


def ctx(lang="en"):
    return IdentificationContext(lang=lang, client_hash="client-1")


def codes(response):
    return {w.code for w in response.warnings}


def baetis_vision(confidence=AIConfidence.high, name="Baetis", rank=TaxonRank.genus, quality=ImageQuality.good, subject=SubjectType.real_organism):
    return OrganismVisionResult(
        subject_type=subject, image_quality=quality, life_stage=LifeStage.nymph, life_stage_confidence=AIConfidence.moderate,
        colors=["brown"],
        candidates=[
            TaxonCandidate(scientific_name=name, rank=rank, order="Ephemeroptera", family="Baetidae", genus="Baetis",
                           confidence=confidence, visual_evidence="two tails, gills"),
            TaxonCandidate(scientific_name="Heptageniidae", rank=TaxonRank.family, order="Ephemeroptera", family="Heptageniidae",
                           confidence=AIConfidence.low, visual_evidence="flattened"),
        ],
    )


GBIF_BAETIS = FakeGbif({"baetis": gbif_exact("Baetis", "genus", order="Ephemeroptera", family="Baetidae", genus="Baetis", class_name="Insecta"),
                        "heptageniidae": gbif_exact("Heptageniidae", "family", order="Ephemeroptera", family="Heptageniidae")})


# --------------------------------------------------------------- Function A
def test_organism_happy_path(make_container):
    container = make_container(analyzer=FakeAnalyzer(organism=baetis_vision()), gbif=GBIF_BAETIS)
    response = container.organism_service.identify(make_image_bytes(), ctx())
    assert response.match_level == MatchLevel.high_match
    assert response.primary.scientific_name == "Baetis" and response.primary.taxonomy_verified
    assert response.primary.in_catalog and response.primary.catalog_organism.scientific_name == "Baetis"
    assert [a.scientific_name for a in response.alternatives] == ["Heptageniidae"]
    assert response.life_stage == LifeStage.nymph
    first = response.recommendations[0]
    assert first.tier == RecommendationTier.biological_same_stage and first.fly.slug == "pheasant-tail-nymph"
    assert "relations_unverified" in codes(response)  # curated relations are not expert-verified yet
    assert {s.name for s in response.sources} >= {"fake", "gbif", "catalog"}
    assert response.identification_id is not None
    stored = container.identifications.list_for_client("client-1", 5)
    assert stored[0].primary_label == "Baetis" and stored[0].candidates[0].organism_id == organism_id(container.snapshots.get(), "Baetis")


def test_species_outside_catalog_uses_ancestors_and_warns(make_container):
    vision = baetis_vision(name="Baetis rhodani", rank=TaxonRank.species)
    gbif = FakeGbif({"baetis rhodani": gbif_exact("Baetis rhodani", "species", order="Ephemeroptera", family="Baetidae", genus="Baetis")})
    response = make_container(analyzer=FakeAnalyzer(organism=vision), gbif=gbif).organism_service.identify(make_image_bytes(), ctx())
    assert not response.primary.in_catalog
    assert {"not_in_catalog", "species_level_uncertain"} <= codes(response)
    assert response.recommendations and response.recommendations[0].matched_organism.scientific_name == "Baetis"


def test_name_not_confirmed_by_gbif_is_downgraded(make_container):
    container = make_container(analyzer=FakeAnalyzer(organism=baetis_vision(name="Baetis inventus", rank=TaxonRank.species)), gbif=FakeGbif())
    response = container.organism_service.identify(make_image_bytes(), ctx())
    assert response.match_level == MatchLevel.moderate_match
    assert "taxonomy_not_matched" in codes(response)
    assert not response.primary.taxonomy_verified


def test_gbif_down_is_reported_but_not_fatal(make_container):
    container = make_container(analyzer=FakeAnalyzer(organism=baetis_vision()), gbif=FakeGbif(down=True))
    response = container.organism_service.identify(make_image_bytes(), ctx())
    assert response.match_level == MatchLevel.high_match
    assert "taxonomy_unavailable" in codes(response)


@pytest.mark.parametrize(
    ("vision", "level", "warning"),
    [
        (baetis_vision(subject=SubjectType.artificial_fly), MatchLevel.not_compatible, "wrong_subject_organism"),
        (baetis_vision(subject=SubjectType.other), MatchLevel.not_compatible, "no_subject"),
        (baetis_vision(quality=ImageQuality.unusable), MatchLevel.insufficient_image, "insufficient_image"),
        (OrganismVisionResult(subject_type=SubjectType.real_organism, image_quality=ImageQuality.poor, candidates=[]), MatchLevel.inconclusive, "inconclusive_identification"),
    ],
)
def test_organism_uncertain_outcomes(make_container, vision, level, warning):
    response = make_container(analyzer=FakeAnalyzer(organism=vision), gbif=GBIF_BAETIS).organism_service.identify(make_image_bytes(), ctx())
    assert response.match_level == level
    assert warning in codes(response)
    if level != MatchLevel.inconclusive:
        assert response.primary is None and response.recommendations == []


def test_ai_down_falls_back_to_visual_similarity(make_container, snapshot):
    hit = VectorHit(uuid.uuid4(), "organism", organism_id(snapshot, "Baetidae"), 0.7)
    container = make_container(
        analyzer=FakeAnalyzer(error=ProviderUnavailableError("gemini", "down", code="ai_timeout")),
        vector_index=FakeVectorIndex({"organism": [hit]}),
    )
    response = container.organism_service.identify(make_image_bytes(), ctx("es"))
    assert response.match_level == MatchLevel.inconclusive  # visual similarity alone is not an identification
    assert response.primary is None
    assert response.visually_similar_organisms[0].organism.scientific_name == "Baetidae"
    assert "ai_unavailable" in codes(response)
    assert "IA" in next(w.message for w in response.warnings if w.code == "ai_unavailable")
    assert response.analysis.ai_available is False


def test_invalid_ai_answer_is_discarded(make_container):
    container = make_container(analyzer=FakeAnalyzer(error=ProviderResponseError("gemini", "bad")))
    assert "ai_bad_response" in codes(container.organism_service.identify(make_image_bytes(), ctx()))


def test_everything_down_raises_503(make_container):
    container = make_container(analyzer=FakeAnalyzer(available=False), embedder=FakeEmbedder(available=False))
    with pytest.raises(ProviderUnavailableError) as exc:
        container.organism_service.identify(make_image_bytes(), ctx())
    assert exc.value.code == "analysis_unavailable"


def test_embedding_failure_is_not_fatal(make_container):
    container = make_container(analyzer=FakeAnalyzer(organism=baetis_vision()), embedder=FakeEmbedder(fail=True), gbif=GBIF_BAETIS)
    response = container.organism_service.identify(make_image_bytes(), ctx())
    assert response.match_level == MatchLevel.high_match and "embeddings_unavailable" in codes(response)


# --------------------------------------------------------------- Function B
def fly_vision(name="Pheasant Tail Nymph", confidence=AIConfidence.high, subject=SubjectType.artificial_fly, attractor=False):
    return FlyVisionResult(
        subject_type=subject, image_quality=ImageQuality.good, category=FlyCategory.nymph, is_attractor_likely=attractor,
        candidates=[FlyPatternCandidate(pattern_name=name, confidence=confidence, visual_evidence="pheasant fibres"),
                    FlyPatternCandidate(pattern_name="Frenchie", confidence=AIConfidence.low, visual_evidence="hot spot")],
        imitation_hints=[ImitationHint(organism_group="Baetidae", life_stage=LifeStage.nymph, confidence=AIConfidence.moderate)],
    )


def test_fly_happy_path(make_container, snapshot):
    analyzer = FakeAnalyzer(fly=fly_vision())
    container = make_container(analyzer=analyzer)
    response = container.fly_service.identify(make_image_bytes(), ctx(), country="AR")
    assert response.match_level == MatchLevel.high_match
    assert response.primary.fly.slug == "pheasant-tail-nymph" and response.primary.name_match == "exact"
    assert response.alternatives[0].pattern_name == "Frenchie"
    assert {"Baetidae", "Baetis"} <= {i.organism.scientific_name for i in response.imitates}
    assert response.ai_imitation_hints[0].catalog_organism.scientific_name == "Baetidae"
    assert response.variants and response.products == []
    assert "Pheasant Tail Nymph" in analyzer.calls[0][1]  # catalog names are given to the model


def test_fly_outside_catalog_is_shown_but_not_verified(make_container):
    response = make_container(analyzer=FakeAnalyzer(fly=fly_vision(name="Purple Haze"))).fly_service.identify(make_image_bytes(), ctx())
    assert response.primary.pattern_name == "Purple Haze" and not response.primary.in_catalog
    assert response.match_level == MatchLevel.moderate_match
    assert "not_in_catalog" in codes(response) and response.imitates == []


def test_attractor_is_not_forced_onto_an_organism(make_container):
    response = make_container(analyzer=FakeAnalyzer(fly=fly_vision(name="Royal Wulff", attractor=True))).fly_service.identify(make_image_bytes(), ctx())
    assert response.primary.fly.slug == "royal-wulff"
    assert response.imitates == [] and "attractor_pattern" in codes(response)


def test_real_insect_photo_in_fly_mode(make_container):
    response = make_container(analyzer=FakeAnalyzer(fly=fly_vision(subject=SubjectType.real_organism))).fly_service.identify(make_image_bytes(), ctx())
    assert response.match_level == MatchLevel.not_compatible and "wrong_subject_fly" in codes(response)
    assert response.primary is None


def test_fly_visual_only_when_ai_is_down(make_container, snapshot):
    hits = [VectorHit(uuid.uuid4(), "fly", fly_id(snapshot, "adams"), 0.9), VectorHit(uuid.uuid4(), "fly", fly_id(snapshot, "comparadun"), 0.6)]
    container = make_container(analyzer=FakeAnalyzer(available=False), vector_index=FakeVectorIndex({"fly": hits}))
    response = container.fly_service.identify(make_image_bytes(), ctx())
    assert response.primary.fly.slug == "adams" and response.primary.evidence == ["visual"]
    assert response.primary.ai_confidence is None
    assert response.match_level == MatchLevel.low_match


def test_demo_mode_flags_everything(make_container):
    from app.services.ai.demo import DemoVisionAnalyzer

    container = make_container(analyzer=DemoVisionAnalyzer(), embedder=FakeEmbedder(available=False), demo_mode=True)
    response = container.organism_service.identify(make_image_bytes(), ctx())
    assert response.analysis.is_demo and "demo_mode" in codes(response)
    dark = container.organism_service.identify(make_image_bytes(dark=True), ctx())
    assert dark.match_level == MatchLevel.insufficient_image
