"""Function B: identify an artificial fly and what real organisms it imitates."""

from __future__ import annotations

import uuid

from app.core.errors import ProviderUnavailableError
from app.models.enums import MatchType
from app.repositories.catalog_snapshot import CatalogSnapshot
from app.repositories.identification_store import CandidateRow
from app.repositories.vector_index import VectorHit
from app.schemas.ai import FlyFeatures, FlyVisionResult, SubjectType
from app.schemas.identification import (
    AIImitationHint,
    EvidenceSource,
    FlyCandidate,
    FlyIdentificationResponse,
    MatchLevel,
)
from app.services.commerce.products import ProductService
from app.services.i18n import color_name
from app.services.identification.common import IdentificationContext, IdentificationPipeline, PipelineDeps
from app.services.identification.confidence import fly_level, gate_subject, visual_only_level

_MAX_CANDIDATES = 6


def _localized_features(features: FlyFeatures, lang: str) -> FlyFeatures:
    """The model writes colours in English (they are matched against the catalog); show them translated."""
    return features.model_copy(update={"colors": [color_name(c, lang) for c in features.colors]})


class FlyIdentificationService(IdentificationPipeline):
    kind = "fly"

    # OpenCLIP ViT-B-32 scores almost any tied fly 0.83-0.93 against any catalog fly photo (evaluation
    # 2026-10-31: unrelated patterns reached 0.905), so visual evidence alone rarely justifies a pattern.
    def __init__(self, deps: PipelineDeps, products: ProductService, visual_strong_threshold: float = 0.95):
        super().__init__(deps)
        self._products = products
        self._visual_strong = visual_strong_threshold

    def _candidates(self, vision: FlyVisionResult | None, hits: list[VectorHit], snapshot: CatalogSnapshot) -> list[FlyCandidate]:
        visual = {h.owner_id: h.similarity for h in hits}
        seen: set[uuid.UUID] = set()
        candidates: list[FlyCandidate] = []
        for proposal in vision.candidates if vision else []:
            found = snapshot.find_fly_by_name(proposal.pattern_name)
            fly, name_match = found if found else (None, "none")
            if fly and fly.id in seen:
                continue
            similarity = visual.get(fly.id) if fly else None
            candidates.append(
                FlyCandidate(
                    rank_position=len(candidates) + 1, pattern_name=fly.name if fly else proposal.pattern_name,
                    fly=snapshot.fly_summary(fly) if fly else None, in_catalog=fly is not None,
                    ai_confidence=proposal.confidence, name_match=name_match,
                    visual_similarity=round(similarity, 4) if similarity is not None else None,
                    evidence=["ai"] + (["visual"] if similarity is not None else []),
                )
            )
            if fly:
                seen.add(fly.id)
        for hit in hits:
            if hit.owner_id in seen or hit.owner_id not in snapshot.flies:
                continue
            fly = snapshot.flies[hit.owner_id]
            candidates.append(
                FlyCandidate(
                    rank_position=len(candidates) + 1, pattern_name=fly.name, fly=snapshot.fly_summary(fly), in_catalog=True,
                    ai_confidence=None, name_match=None, visual_similarity=round(hit.similarity, 4), evidence=["visual"],
                )
            )
            seen.add(fly.id)
        return candidates[:_MAX_CANDIDATES]

    def identify(self, data: bytes, ctx: IdentificationContext, country: str | None = None) -> FlyIdentificationResponse:
        image = self.prepare(data, ctx)
        snapshot = self.deps.snapshots.get()
        known_patterns = snapshot.fly_names()
        vision: FlyVisionResult | None = self.run_ai(lambda: self.deps.analyzer.analyze_fly(image, known_patterns, ctx.lang), ctx)
        vector = self.embed(image, ctx)
        if vision is None and vector is None:
            raise ProviderUnavailableError("analysis", "Image analysis is temporarily unavailable. Please try again later.", code="analysis_unavailable")

        hits = [h for h in self.similar("fly", vector, 10) if h.owner_id in snapshot.flies]
        response = FlyIdentificationResponse(
            identification_id=None, match_level=MatchLevel.inconclusive, subject_type=vision.subject_type if vision else None,
            image_quality=vision.image_quality if vision else None, primary=None, alternatives=[],
            category=vision.category if vision else None, features=_localized_features(vision.features, ctx.lang) if vision else None,
            is_attractor_likely=vision.is_attractor_likely if vision else False, imitates=[], ai_imitation_hints=[],
            variants=[], products=[], sources=[], warnings=[], analysis=self.analysis_info(ctx),
        )

        gate = gate_subject(vision.subject_type, vision.image_quality, SubjectType.artificial_fly) if vision else None
        if gate is not None:
            response.match_level = gate
            if gate == MatchLevel.insufficient_image:
                ctx.warn("insufficient_image", issues=", ".join(vision.image_quality_issues) or "-")
            elif vision.subject_type == SubjectType.real_organism:
                ctx.warn("wrong_subject_fly")
            else:
                ctx.warn("no_subject")
        else:
            self._fill(response, vision, hits, snapshot, ctx, country)

        response.warnings = ctx.warnings
        response.analysis = self.analysis_info(ctx)
        all_candidates = [response.primary, *response.alternatives] if response.primary else []
        response.identification_id = self.log(
            ctx, image, response, response.primary.pattern_name if response.primary else None,
            [
                CandidateRow(
                    position=c.rank_position, label=c.pattern_name, fly_pattern_id=c.fly.id if c.fly else None,
                    ai_confidence=c.ai_confidence.value if c.ai_confidence else None, visual_similarity=c.visual_similarity,
                )
                for c in all_candidates
            ],
        )
        return response

    def _fill(self, response, vision, hits, snapshot: CatalogSnapshot, ctx: IdentificationContext, country: str | None) -> None:
        candidates = self._candidates(vision, hits, snapshot)
        if ctx.ai_available:
            response.sources.append(EvidenceSource(name=self.deps.analyzer.provider, detail=self.deps.analyzer.model))
        if hits:
            response.sources.append(EvidenceSource(name="visual_similarity", detail=self.deps.embedder.model_id))
        if not candidates:
            response.match_level = MatchLevel.inconclusive
            ctx.warn("inconclusive_identification")
            return

        primary, *alternatives = candidates
        response.primary, response.alternatives = primary, alternatives
        if vision is None or primary.ai_confidence is None:
            response.match_level = visual_only_level(primary.visual_similarity, self._visual_strong)
        else:
            response.match_level = fly_level(
                primary.ai_confidence, quality=vision.image_quality, in_catalog=primary.in_catalog,
                fuzzy_name=primary.name_match == "fuzzy",
            )
        if primary.name_match == "fuzzy":
            ctx.warn("fuzzy_pattern_name", name=primary.pattern_name)
        if not primary.in_catalog:
            ctx.warn("not_in_catalog", name=primary.pattern_name)

        if vision:
            response.ai_imitation_hints = [
                AIImitationHint(
                    organism_group=hint.organism_group, life_stage=hint.life_stage, ai_confidence=hint.confidence,
                    catalog_organism=(
                        snapshot.organism_summary(found, ctx.lang) if (found := snapshot.find_organism_by_group(hint.organism_group)) else None
                    ),
                )
                for hint in vision.imitation_hints
            ]

        if primary.fly is None:
            return
        fly = snapshot.flies[primary.fly.id]
        response.sources.append(EvidenceSource(name="catalog", detail=fly.name))
        response.imitates = snapshot.imitated_organisms(fly.id, ctx.lang)
        response.variants = list(fly.variants)
        response.products = self._products.for_fly(fly.id, country)
        if fly.imitation_type == MatchType.attractor or response.is_attractor_likely:
            ctx.warn("attractor_pattern")
        if any(not relation.expert_verified for relation in response.imitates):
            ctx.warn("relations_unverified")
