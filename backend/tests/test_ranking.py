import uuid

from app.models.enums import RANK_LEVEL, LifeStage, TaxonRank
from app.repositories.vector_index import VectorHit
from app.schemas.identification import RecommendationTier
from app.services.recommendations.ranking import RankingConfig, RankingInput, RecommendationEngine, color_overlap
from tests.conftest import fly_id


def recommend(snapshot, names, stage, *, rank=TaxonRank.genus, colors=(), hits=()):
    engine = RecommendationEngine()
    data = RankingInput(
        lineage=snapshot.resolve_lineage(names), identified_rank_level=RANK_LEVEL[rank], observed_stage=stage,
        observed_colors=list(colors), fly_visual_hits=list(hits),
    )
    return engine.recommend(snapshot, data, "en")


def test_same_stage_relations_come_first(snapshot):
    recs = recommend(snapshot, ["Baetis", "Baetidae", "Ephemeroptera"], LifeStage.nymph)
    tiers = [r.tier for r in recs]
    assert tiers == sorted(tiers, key=lambda t: list(RecommendationTier).index(t) if t != RecommendationTier.biological_stage_unknown else 1)
    assert recs[0].tier == RecommendationTier.biological_same_stage
    assert recs[0].fly.slug == "pheasant-tail-nymph"
    assert recs[0].life_stage == LifeStage.nymph


def test_unknown_stage_does_not_claim_a_stage_match(snapshot):
    recs = recommend(snapshot, ["Baetis"], LifeStage.unknown)
    assert recs and all(r.tier == RecommendationTier.biological_stage_unknown for r in recs)


def test_specific_relation_beats_broader_group(snapshot):
    recs = recommend(snapshot, ["Baetis", "Baetidae", "Ephemeroptera"], LifeStage.subimago)
    by_slug = {r.fly.slug: r for r in recs}
    assert by_slug["blue-winged-olive"].components.taxonomic_specificity == 1.0
    assert by_slug["adams"].components.taxonomic_specificity < 1.0  # only documented for Ephemeroptera
    assert by_slug["blue-winged-olive"].ranking_score > by_slug["adams"].ranking_score
    assert "broader group" in by_slug["adams"].reasons[0]


def test_visual_similarity_never_outranks_biology(snapshot):
    zebra = fly_id(snapshot, "merkin-crab")  # biologically unrelated to mayflies
    hits = [VectorHit(uuid.uuid4(), "fly", zebra, 0.99)]
    recs = recommend(snapshot, ["Baetis"], LifeStage.nymph, hits=hits)
    assert recs[-1].fly.slug == "merkin-crab"
    assert recs[-1].tier == RecommendationTier.visual_only
    assert recs[-1].matched_organism is None
    assert "not a probability" in recs[-1].reasons[-1]


def test_weak_visual_only_hits_are_dropped(snapshot):
    hits = [VectorHit(uuid.uuid4(), "fly", fly_id(snapshot, "merkin-crab"), 0.1)]
    assert all(r.fly.slug != "merkin-crab" for r in recommend(snapshot, ["Baetis"], LifeStage.nymph, hits=hits))


def test_scores_are_bounded_and_components_kept_separate(snapshot):
    hits = [VectorHit(uuid.uuid4(), "fly", fly_id(snapshot, "pheasant-tail-nymph"), 0.4)]
    recs = recommend(snapshot, ["Baetis"], LifeStage.nymph, colors=["brown"], hits=hits)
    pt = next(r for r in recs if r.fly.slug == "pheasant-tail-nymph")
    assert 0 <= pt.ranking_score <= 1
    assert pt.visual_similarity == 0.4  # raw cosine kept apart from the score
    assert pt.components.biological == RankingConfig().compatibility[pt.biological_compatibility]
    assert pt.components.color == 1.0


def test_no_relations_means_no_biological_recommendations(snapshot):
    assert recommend(snapshot, ["Caenidae"], LifeStage.subimago) == []


def test_color_overlap_uses_color_families(snapshot):
    fly = next(f for f in snapshot.flies.values() if f.slug == "pale-morning-dun")
    score, shared = color_overlap(["Sulphur", "grey"], fly)
    assert shared == ["yellow"] and score == 0.5
    assert color_overlap([], fly) == (None, [])


def test_relatives_in_same_order_fill_in_when_taxon_has_no_relations(snapshot):
    """A dragonfly nymph identified only as "Anisoptera" (not in the catalog) gets Aeshnidae's flies."""
    engine = RecommendationEngine()
    adams = VectorHit(uuid.uuid4(), "fly", fly_id(snapshot, "adams"), 0.75)
    data = RankingInput(
        lineage=snapshot.resolve_lineage(["Anisoptera"]), identified_rank_level=RANK_LEVEL[TaxonRank.suborder],
        observed_stage=LifeStage.nymph, observed_colors=[], fly_visual_hits=[adams],
        relatives=snapshot.organisms_in_order("Odonata"),
    )
    recs = engine.recommend(snapshot, data, "en")
    # The catalog has no suborders, so both Odonata nymph patterns qualify.
    assert {r.fly.slug for r in recs[:2]} == {"dragonfly-nymph", "damsel-nymph"}
    assert recs[0].tier == RecommendationTier.related_taxon and "same order (Odonata)" in recs[0].reasons[0]
    assert recs[-1].fly.slug == "adams" and recs[-1].tier == RecommendationTier.visual_only


def test_relatives_are_ignored_when_lineage_has_relations(snapshot):
    engine = RecommendationEngine()
    data = RankingInput(
        lineage=snapshot.resolve_lineage(["Baetidae"]), identified_rank_level=RANK_LEVEL[TaxonRank.family],
        observed_stage=LifeStage.nymph, observed_colors=[], fly_visual_hits=[],
        relatives=snapshot.organisms_in_order("Ephemeroptera"),
    )
    assert all(r.tier != RecommendationTier.related_taxon for r in engine.recommend(snapshot, data, "en"))
