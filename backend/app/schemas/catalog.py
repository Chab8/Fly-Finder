"""API response shapes for catalog browsing (organisms, fly patterns, relations)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel

from app.models.catalog import CommonName, Material, Variant
from app.models.enums import (
    BiologicalCompatibility,
    FishingEnvironment,
    FlyCategory,
    Habitat,
    LifeStage,
    MatchType,
    OrganismGroup,
    TaxonRank,
    VerificationStatus,
)


class ImageInfo(BaseModel):
    id: uuid.UUID
    url: str
    source: str
    source_url: str | None
    license: str
    attribution: str
    image_view: str | None
    life_stage: LifeStage | None


class OrganismSummary(BaseModel):
    id: uuid.UUID
    scientific_name: str
    common_name: str | None
    taxonomic_rank: TaxonRank
    order: str | None
    family: str | None
    genus: str | None
    organism_group: OrganismGroup
    thumbnail_url: str | None
    is_demo: bool


class Taxonomy(BaseModel):
    kingdom: str | None
    phylum: str | None
    class_name: str | None
    order: str | None
    family: str | None
    genus: str | None
    species: str | None


class FlyPatternSummary(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    category: FlyCategory
    imitation_type: MatchType
    hook_size_min: str | None
    hook_size_max: str | None
    colors: list[str]
    thumbnail_url: str | None
    is_demo: bool


class RelationInfo(BaseModel):
    """A documented organism <-> fly relationship from fly_organism_matches."""

    life_stage: LifeStage
    match_type: MatchType
    biological_compatibility: BiologicalCompatibility
    expert_verified: bool
    verification_source: str | None
    notes: str | None


class ImitatingFly(RelationInfo):
    fly: FlyPatternSummary


class ImitatedOrganism(RelationInfo):
    organism: OrganismSummary


class OrganismDetail(OrganismSummary):
    taxonomy: Taxonomy
    gbif_taxon_id: int | None
    inaturalist_taxon_id: int | None
    common_names: list[CommonName]
    synonyms: list[str]
    habitats: list[Habitat]
    life_stages: list[LifeStage]
    size_min: Decimal | None
    size_max: Decimal | None
    size_unit: str | None
    geographic_distribution: str | None
    description: str | None
    fishing_notes: str | None
    text_language: str | None
    images: list[ImageInfo]
    imitated_by: list[ImitatingFly]
    data_source: str
    verification_status: VerificationStatus


class FlyPatternDetail(FlyPatternSummary):
    alternate_names: list[str]
    materials: list[Material]
    variants: list[Variant]
    habitats: list[Habitat]
    fishing_environments: list[FishingEnvironment]
    difficulty: str | None
    description: str | None
    usage_notes: str | None
    text_language: str | None
    images: list[ImageInfo]
    imitates: list[ImitatedOrganism]
    product_count: int
    data_source: str
    verification_status: VerificationStatus


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int


class SearchResults(BaseModel):
    query: str
    organisms: list[OrganismSummary]
    flies: list[FlyPatternSummary]
