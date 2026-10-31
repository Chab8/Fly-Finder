"""Function A: identify a real organism and recommend artificial flies that imitate it."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from app.core.errors import ProviderUnavailableError
from app.models.enums import RANK_LEVEL, LifeStage, TaxonRank
from app.repositories.catalog_snapshot import CatalogSnapshot
from app.repositories.identification_store import CandidateRow
from app.schemas.ai import AIConfidence, OrganismVisionResult, SubjectType, TaxonCandidate
from app.schemas.identification import (
    EvidenceSource,
    MatchLevel,
    OrganismCandidate,
    OrganismIdentificationResponse,
    RecommendationTier,
    SimilarCatalogOrganism,
    TaxonomyMatch,
    VisualFeatures,
)
from app.services.identification.common import IdentificationContext, IdentificationPipeline, PipelineDeps
from app.services.identification.confidence import gate_subject, organism_level, visual_only_level
from app.services.recommendations.ranking import RankingInput, RecommendationEngine
from app.services.taxonomy.gbif import GbifClient

logger = logging.getLogger(__name__)
_MAX_CANDIDATES = 5
# Only EXACT counts as confirmation. FUZZY matches can land on unrelated taxa
# (e.g. "Hirudinea" -> the bird genus "Hirundinea"), HIGHERRANK only confirms a parent.
_VERIFIED_MATCH_TYPES = {"EXACT"}


class OrganismIdentificationService(IdentificationPipeline):
    kind = "organism"

    def __init__(self, deps: PipelineDeps, gbif: GbifClient | None, engine: RecommendationEngine, visual_strong_threshold: float = 0.85):
        super().__init__(deps)
        self._gbif = gbif
        self._engine = engine
        self._visual_strong = visual_strong_threshold

    # ------------------------------------------------------------- taxonomy
    def _lookup_taxonomy(self, candidates: list[TaxonCandidate], ctx: IdentificationContext) -> list[TaxonomyMatch | None | Exception]:
        if self._gbif is None or self.deps.demo_mode:
            return [None] * len(candidates)

        def lookup(candidate: TaxonCandidate):
            try:
                return self._gbif.match(candidate.scientific_name, rank=candidate.rank.value)
            except ProviderUnavailableError as exc:
                return exc

        with ThreadPoolExecutor(max_workers=min(4, len(candidates) or 1)) as pool:
            results = list(pool.map(lookup, candidates))
        if any(isinstance(r, Exception) for r in results):
            ctx.warn("taxonomy_unavailable")
        return results

    def _resolve_candidates(self, vision: OrganismVisionResult, snapshot: CatalogSnapshot, ctx: IdentificationContext) -> list[OrganismCandidate]:
        raw = vision.candidates[:_MAX_CANDIDATES]
        taxonomies = self._lookup_taxonomy(raw, ctx)
        resolved: list[OrganismCandidate] = []
        for position, (candidate, taxonomy) in enumerate(zip(raw, taxonomies, strict=True), start=1):
            match = taxonomy if isinstance(taxonomy, TaxonomyMatch) else None
            verified = bool(match and match.match_type in _VERIFIED_MATCH_TYPES)
            organism = snapshot.find_organism_by_name(candidate.scientific_name) or (
                snapshot.find_organism_by_name(match.accepted_name) if verified and match.accepted_name else None
            )
            resolved.append(
                OrganismCandidate(
                    rank_position=position,
                    scientific_name=candidate.scientific_name,
                    taxonomic_rank=candidate.rank,
                    common_name=(snapshot.common_name(organism, ctx.lang) if organism else None) or candidate.common_name_en,
                    order=(match.order if verified else None) or candidate.order,
                    family=(match.family if verified else None) or candidate.family,
                    genus=(match.genus if verified else None) or candidate.genus,
                    ai_confidence=candidate.confidence,
                    visual_evidence=candidate.visual_evidence,
                    taxonomy=match,
                    taxonomy_verified=verified,
                    catalog_organism=snapshot.organism_summary(organism, ctx.lang) if organism else None,
                    in_catalog=organism is not None,
                )
            )
        return resolved

    @staticmethod
    def _lineage_names(candidate: OrganismCandidate) -> list[str]:
        """Taxon names from most to least specific, used to find catalog relations."""
        names = [candidate.scientific_name]
        taxonomy = candidate.taxonomy if candidate.taxonomy_verified else None
        if taxonomy and taxonomy.accepted_name:
            names.append(taxonomy.accepted_name)
        names += [candidate.genus, candidate.family, candidate.order]
        if taxonomy:
            names += [taxonomy.class_name]
        return [n for n in names if n]

    # ------------------------------------------------------------- main flow
    def identify(self, data: bytes, ctx: IdentificationContext) -> OrganismIdentificationResponse:
        image = self.prepare(data, ctx)
        vision: OrganismVisionResult | None = self.run_ai(lambda: self.deps.analyzer.analyze_organism(image), ctx)
        vector = self.embed(image, ctx)
        if vision is None and vector is None:
            raise ProviderUnavailableError("analysis", "Image analysis is temporarily unavailable. Please try again later.", code="analysis_unavailable")

        snapshot = self.deps.snapshots.get()
        organism_hits = [h for h in self.similar("organism", vector, 5) if h.owner_id in snapshot.organisms]
        similar = [
            SimilarCatalogOrganism(organism=snapshot.organism_summary(snapshot.organisms[h.owner_id], ctx.lang), visual_similarity=round(h.similarity, 4))
            for h in organism_hits
        ]
        sources = []
        if ctx.ai_available:
            sources.append(EvidenceSource(name=self.deps.analyzer.provider, detail=self.deps.analyzer.model))
        if similar:
            sources.append(EvidenceSource(name="visual_similarity", detail=self.deps.embedder.model_id))

        response = OrganismIdentificationResponse(
            identification_id=None, match_level=MatchLevel.inconclusive, subject_type=None, image_quality=None,
            primary=None, alternatives=[], life_stage=LifeStage.unknown, life_stage_confidence=AIConfidence.none,
            visual_features=None, recommendations=[], visually_similar_organisms=similar, sources=sources,
            warnings=[], analysis=self.analysis_info(ctx),
        )

        if vision is None:
            response.match_level = visual_only_level(similar[0].visual_similarity if similar else None, self._visual_strong)
        else:
            self._fill_from_vision(response, vision, snapshot, vector, ctx)

        response.warnings = ctx.warnings
        response.analysis = self.analysis_info(ctx)
        candidates = [response.primary, *response.alternatives] if response.primary else []
        response.identification_id = self.log(
            ctx, image, response, response.primary.scientific_name if response.primary else None,
            [
                CandidateRow(
                    position=c.rank_position, label=c.scientific_name,
                    organism_id=c.catalog_organism.id if c.catalog_organism else None, ai_confidence=c.ai_confidence.value,
                )
                for c in candidates
            ],
        )
        return response

    def _fill_from_vision(self, response, vision: OrganismVisionResult, snapshot: CatalogSnapshot, vector, ctx: IdentificationContext) -> None:
        response.subject_type = vision.subject_type
        response.image_quality = vision.image_quality
        gate = gate_subject(vision.subject_type, vision.image_quality, SubjectType.real_organism)
        if gate is not None:
            response.match_level = gate
            if gate == MatchLevel.insufficient_image:
                ctx.warn("insufficient_image", issues=", ".join(vision.image_quality_issues) or "-")
            elif vision.subject_type == SubjectType.artificial_fly:
                ctx.warn("wrong_subject_organism")
            else:
                ctx.warn("no_subject")
            return

        response.life_stage = vision.life_stage if vision.life_stage_confidence != AIConfidence.none else LifeStage.unknown
        response.life_stage_confidence = vision.life_stage_confidence
        response.visual_features = VisualFeatures(
            colors=vision.colors, morphological_features=vision.morphological_features,
            estimated_length_mm=vision.estimated_length_mm if vision.size_reference else None,
            size_reference=vision.size_reference, habitat_hint=vision.habitat_hint,
        )
        candidates = self._resolve_candidates(vision, snapshot, ctx)
        if not candidates:
            response.match_level = MatchLevel.inconclusive
            ctx.warn("inconclusive_identification")
            return

        primary, *alternatives = candidates
        response.primary, response.alternatives = primary, alternatives
        gbif_answered = self._gbif is not None and not self.deps.demo_mode and "taxonomy_unavailable" not in {w.code for w in ctx.warnings}
        # GBIF answered but did not confirm the name (no match, or only a broader taxon).
        name_rejected = gbif_answered and not primary.taxonomy_verified
        response.match_level = organism_level(primary.ai_confidence, quality=vision.image_quality, name_rejected_by_gbif=name_rejected)
        if name_rejected:
            ctx.warn("taxonomy_not_matched", name=primary.scientific_name)
        if primary.taxonomy_verified:
            response.sources.append(EvidenceSource(name="gbif", detail=primary.taxonomy.accepted_name, url=primary.taxonomy.url))
        if primary.taxonomic_rank in (TaxonRank.species, TaxonRank.subspecies):
            ctx.warn("species_level_uncertain")
        if not primary.in_catalog:
            ctx.warn("not_in_catalog", name=primary.scientific_name)

        lineage = snapshot.resolve_lineage(self._lineage_names(primary))
        fly_hits = self.similar("fly", vector, 20)
        response.recommendations = self._engine.recommend(
            snapshot,
            RankingInput(
                lineage=lineage, identified_rank_level=RANK_LEVEL[primary.taxonomic_rank],
                observed_stage=response.life_stage, observed_colors=vision.colors, fly_visual_hits=fly_hits,
            ),
            ctx.lang,
        )
        if lineage:
            response.sources.append(EvidenceSource(name="catalog", detail=lineage[0].scientific_name))
        biological = [r for r in response.recommendations if r.tier != RecommendationTier.visual_only]
        if not biological:
            ctx.warn("no_recommendations")
        elif any(not r.expert_verified for r in biological):
            ctx.warn("relations_unverified")
