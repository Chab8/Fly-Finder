"""Fly recommendation ranking for a real organism (Function A).

Methodology (docs/AI_PIPELINE.md#ranking):
1. Candidate flies come from documented relations (fly_organism_matches) for the
   identified taxon AND its catalog ancestors (genus -> family -> order).
2. Flies are grouped into tiers that are never mixed: documented relation at the
   observed life stage, at an unknown stage, at another stage, then visual-only.
   A visually similar fly never outranks a biologically documented one.
3. Inside a tier, flies are ordered by a weighted mean of the components that are
   available for that fly. All weights and scores below are EXPERIMENTAL HEURISTICS
   (version RANKING_VERSION) that must be calibrated with the evaluation set. They are
   not scientific truths and the resulting score is not a probability.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from app.models.catalog import FlyRecord, MatchRecord, OrganismRecord
from app.models.enums import RANK_LEVEL, BiologicalCompatibility, LifeStage, MatchType
from app.repositories.catalog_snapshot import CatalogSnapshot
from app.repositories.vector_index import VectorHit
from app.schemas.identification import FlyRecommendation, RecommendationTier, ScoreComponents
from app.services.i18n import stage_name, t

RANKING_VERSION = "heuristic-v0.1"

TIER_ORDER = {
    RecommendationTier.biological_same_stage: 0,
    RecommendationTier.biological_stage_unknown: 1,
    RecommendationTier.biological_other_stage: 2,
    RecommendationTier.visual_only: 3,
}

# Stages that are commonly confused or imitated by the same fly get partial credit.
_RELATED_STAGES = [
    {LifeStage.subimago, LifeStage.imago, LifeStage.adult},
    {LifeStage.pupa, LifeStage.emerger},
    {LifeStage.nymph, LifeStage.larva},
]

_COLOR_FAMILIES = {
    "olive": "olive", "olive green": "olive", "green": "green", "chartreuse": "green",
    "brown": "brown", "dark brown": "brown", "rust": "brown", "rusty": "brown", "mahogany": "brown",
    "tan": "tan", "cream": "tan", "beige": "tan", "sand": "tan", "sulphur": "yellow", "yellow": "yellow",
    "pale yellow": "yellow", "golden": "yellow", "gold": "yellow", "orange": "orange",
    "grey": "grey", "gray": "grey", "dun": "grey", "blue dun": "grey", "black": "black", "white": "white",
    "silver": "white", "red": "red", "pink": "pink", "purple": "purple", "blue": "blue", "translucent": "clear",
    "clear": "clear",
}


@dataclass(frozen=True)
class RankingConfig:
    version: str = RANKING_VERSION
    weights: dict[str, float] = field(default_factory=lambda: {
        "biological": 0.40, "taxonomic_specificity": 0.15, "life_stage": 0.25,
        "imitation_type": 0.10, "color": 0.05, "visual": 0.05,
    })
    compatibility: dict[BiologicalCompatibility, float] = field(default_factory=lambda: {
        BiologicalCompatibility.high: 1.0, BiologicalCompatibility.medium: 0.6,
        BiologicalCompatibility.low: 0.3, BiologicalCompatibility.unknown: 0.15,
    })
    imitation: dict[MatchType, float] = field(default_factory=lambda: {
        MatchType.exact_imitation: 1.0, MatchType.general_imitation: 0.75, MatchType.suggestive_imitation: 0.5,
        MatchType.not_specified: 0.4, MatchType.attractor: 0.3,
    })
    stage_exact: float = 1.0
    stage_related: float = 0.6
    stage_unknown: float = 0.5
    stage_mismatch: float = 0.1
    specificity_step: float = 0.1     # lost per rank level between relation taxon and identified taxon
    specificity_floor: float = 0.3
    visual_floor: float = 0.15        # cosine similarity mapped to 0 at this value...
    visual_ceiling: float = 0.60      # ...and to 1 at this value
    visual_only_min_similarity: float = 0.25
    max_results: int = 12


@dataclass
class RankingInput:
    lineage: list[OrganismRecord]          # catalog organisms, most specific first
    identified_rank_level: int             # RANK_LEVEL of the identified taxon
    observed_stage: LifeStage
    observed_colors: list[str]
    fly_visual_hits: list[VectorHit]


def _color_families(colors: list[str]) -> set[str]:
    families = set()
    for color in colors:
        key = color.strip().lower()
        if key:
            families.add(_COLOR_FAMILIES.get(key) or _COLOR_FAMILIES.get(key.split()[-1], key))
    return families


def color_overlap(observed: list[str], fly: FlyRecord) -> tuple[float | None, list[str]]:
    observed_families = _color_families(observed)
    fly_families = _color_families(list(fly.colors))
    if not observed_families or not fly_families:
        return None, []
    shared = sorted(observed_families & fly_families)
    return len(shared) / len(observed_families), shared


def stage_score(config: RankingConfig, observed: LifeStage, relation: LifeStage) -> tuple[float, RecommendationTier]:
    if observed == LifeStage.unknown or relation == LifeStage.unknown:
        return config.stage_unknown, RecommendationTier.biological_stage_unknown
    if observed == relation:
        return config.stage_exact, RecommendationTier.biological_same_stage
    if any(observed in group and relation in group for group in _RELATED_STAGES):
        return config.stage_related, RecommendationTier.biological_other_stage
    return config.stage_mismatch, RecommendationTier.biological_other_stage


def visual_component(config: RankingConfig, similarity: float | None) -> float | None:
    if similarity is None:
        return None
    span = config.visual_ceiling - config.visual_floor
    return max(0.0, min(1.0, (similarity - config.visual_floor) / span))


def weighted_score(config: RankingConfig, components: ScoreComponents) -> float:
    total, weight_sum = 0.0, 0.0
    for name, weight in config.weights.items():
        value = getattr(components, name)
        if value is not None:
            total += weight * value
            weight_sum += weight
    return round(total / weight_sum, 4) if weight_sum else 0.0


class RecommendationEngine:
    def __init__(self, config: RankingConfig | None = None):
        self.config = config or RankingConfig()

    def recommend(self, snapshot: CatalogSnapshot, data: RankingInput, lang: str) -> list[FlyRecommendation]:
        cfg = self.config
        visual_by_fly = {hit.owner_id: hit.similarity for hit in data.fly_visual_hits}
        best: dict[uuid.UUID, FlyRecommendation] = {}

        for organism in data.lineage:
            levels_up = max(0, data.identified_rank_level - RANK_LEVEL[organism.taxonomic_rank])
            specificity = max(cfg.specificity_floor, 1.0 - cfg.specificity_step * levels_up)
            for relation in snapshot.relations_for_organism(organism.id):
                candidate = self._from_relation(snapshot, organism, relation, specificity, data, visual_by_fly, lang)
                current = best.get(relation.fly_pattern_id)
                if current is None or self._sort_key(candidate) < self._sort_key(current):
                    best[relation.fly_pattern_id] = candidate

        for hit in data.fly_visual_hits:
            if hit.owner_id in best or hit.similarity < cfg.visual_only_min_similarity or hit.owner_id not in snapshot.flies:
                continue
            components = ScoreComponents(visual=visual_component(cfg, hit.similarity))
            best[hit.owner_id] = FlyRecommendation(
                fly=snapshot.fly_summary(snapshot.flies[hit.owner_id]), tier=RecommendationTier.visual_only,
                matched_organism=None, life_stage=None, match_type=None, biological_compatibility=None,
                expert_verified=False, visual_similarity=round(hit.similarity, 4),
                ranking_score=weighted_score(cfg, components), components=components,
                reasons=[t("reason_visual_only", lang), t("reason_visual", lang, similarity=f"{hit.similarity:.2f}")],
            )

        return sorted(best.values(), key=self._sort_key)[: cfg.max_results]

    @staticmethod
    def _sort_key(rec: FlyRecommendation) -> tuple:
        return (TIER_ORDER[rec.tier], -rec.ranking_score, rec.fly.name)

    def _from_relation(
        self, snapshot: CatalogSnapshot, organism: OrganismRecord, relation: MatchRecord, specificity: float,
        data: RankingInput, visual_by_fly: dict[uuid.UUID, float], lang: str,
    ) -> FlyRecommendation:
        cfg = self.config
        fly = snapshot.flies[relation.fly_pattern_id]
        stage_value, tier = stage_score(cfg, data.observed_stage, relation.life_stage)
        color_value, shared_colors = color_overlap(data.observed_colors, fly)
        similarity = visual_by_fly.get(fly.id)
        components = ScoreComponents(
            biological=cfg.compatibility[relation.biological_compatibility],
            taxonomic_specificity=specificity,
            life_stage=stage_value,
            imitation_type=cfg.imitation[relation.match_type],
            color=color_value,
            visual=visual_component(cfg, similarity),
        )
        organism_label = organism.scientific_name
        reasons = [
            t("reason_relation", lang, organism=organism_label, stage=stage_name(relation.life_stage.value, lang))
            if organism is data.lineage[0]
            else t("reason_broader_group", lang, organism=organism_label),
        ]
        if tier == RecommendationTier.biological_same_stage:
            reasons.append(t("reason_same_stage", lang))
        elif tier == RecommendationTier.biological_other_stage:
            reasons.append(t("reason_other_stage", lang, stage=stage_name(relation.life_stage.value, lang), observed=stage_name(data.observed_stage.value, lang)))
        reasons.append(
            t("reason_expert_verified", lang, source=relation.verification_source) if relation.expert_verified else t("reason_unverified", lang)
        )
        if shared_colors:
            reasons.append(t("reason_colors", lang, colors=", ".join(shared_colors)))
        if similarity is not None:
            reasons.append(t("reason_visual", lang, similarity=f"{similarity:.2f}"))
        return FlyRecommendation(
            fly=snapshot.fly_summary(fly), tier=tier, matched_organism=snapshot.organism_summary(organism, lang),
            life_stage=relation.life_stage, match_type=relation.match_type,
            biological_compatibility=relation.biological_compatibility, expert_verified=relation.expert_verified,
            visual_similarity=round(similarity, 4) if similarity is not None else None,
            ranking_score=weighted_score(cfg, components), components=components, reasons=reasons,
        )
