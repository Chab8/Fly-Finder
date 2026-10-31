"""Domain records for the catalog.

These are the shapes shared by the CSV importer, the Postgres loader/writer and the
in-memory catalog snapshot. API response shapes live in app/schemas.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

from app.models.enums import (
    AvailabilityStatus,
    BiologicalCompatibility,
    FishingEnvironment,
    FlyCategory,
    Habitat,
    LifeStage,
    MatchType,
    OrganismGroup,
    PermissionStatus,
    TaxonRank,
    VerificationStatus,
)

# Deterministic IDs: the same natural key always yields the same UUID, so re-importing
# a CSV upserts instead of duplicating, and memory/Postgres modes share IDs.
_NAMESPACE = uuid.UUID("6f1b2c1e-4a43-4b8e-9d1f-2f6c3f5b7a10")


def stable_id(kind: str, *natural_key: str) -> uuid.UUID:
    key = "|".join(part.strip().lower() for part in natural_key)
    return uuid.uuid5(_NAMESPACE, f"{kind}:{key}")


_HOOK_SIZE = re.compile(r"^(\d{1,2})(/0)?$")


def hook_size_index(label: str) -> int:
    """Map a hook size label to an index that grows with physical hook size.

    "20" -> -20, "10" -> -10, "1" -> -1, "1/0" -> 1, "4/0" -> 4.
    Hook sizes are not standardized across manufacturers, so this is used only to
    validate ranges, never to infer insect size.
    """
    match = _HOOK_SIZE.match(label.strip())
    if not match:
        raise ValueError(f"invalid hook size label: {label!r}")
    number = int(match.group(1))
    return number if match.group(2) else -number


class Record(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)


class CommonName(Record):
    language: str = Field(pattern=r"^[a-z]{2}$")
    name: str = Field(min_length=1)
    is_primary: bool = False


class LocalizedText(Record):
    language: str = Field(pattern=r"^[a-z]{2}$")
    description: str | None = None
    fishing_notes: str | None = None


class OrganismRecord(Record):
    id: uuid.UUID
    scientific_name: str = Field(min_length=2)
    taxonomic_rank: TaxonRank
    kingdom: str | None = None
    phylum: str | None = None
    class_name: str | None = Field(default=None, alias="class")
    order: str | None = None
    family: str | None = None
    genus: str | None = None
    species: str | None = None
    gbif_taxon_id: int | None = None
    inaturalist_taxon_id: int | None = None
    organism_group: OrganismGroup
    habitats: tuple[Habitat, ...] = ()
    life_stages: tuple[LifeStage, ...] = ()
    size_min: Decimal | None = None
    size_max: Decimal | None = None
    size_unit: Literal["mm"] | None = None
    geographic_distribution: str | None = None
    common_names: tuple[CommonName, ...] = ()
    texts: tuple[LocalizedText, ...] = ()
    synonyms: tuple[str, ...] = ()
    data_source: str = "curated"
    verification_status: VerificationStatus = VerificationStatus.unverified
    is_demo: bool = False

    @model_validator(mode="after")
    def _check(self) -> OrganismRecord:
        if self.taxonomic_rank == TaxonRank.species and len(self.scientific_name.split()) < 2:
            raise ValueError(f"{self.scientific_name}: species rank requires a binomial name")
        if self.size_min is not None and self.size_max is not None and self.size_min > self.size_max:
            raise ValueError(f"{self.scientific_name}: size_min > size_max")
        if (self.size_min is not None or self.size_max is not None) and self.size_unit is None:
            raise ValueError(f"{self.scientific_name}: size requires size_unit")
        return self

    def lineage(self) -> list[tuple[TaxonRank, str]]:
        """Known ancestors (and self) from broad to specific, used for taxonomic matching."""
        pairs = [
            (TaxonRank.kingdom, self.kingdom),
            (TaxonRank.phylum, self.phylum),
            (TaxonRank.class_, self.class_name),
            (TaxonRank.order, self.order),
            (TaxonRank.family, self.family),
            (TaxonRank.genus, self.genus),
            (TaxonRank.species, self.species),
        ]
        return [(rank, name) for rank, name in pairs if name]


class Material(Record):
    component: str = Field(min_length=1)  # hook, thread, tail, body, rib, wing, hackle, head...
    material: str = Field(min_length=1)


class Variant(Record):
    name: str = Field(min_length=1)
    description: str | None = None


class FlyRecord(Record):
    id: uuid.UUID
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    name: str = Field(min_length=2)
    alternate_names: tuple[str, ...] = ()
    category: FlyCategory
    imitation_type: MatchType = MatchType.not_specified
    hook_size_min: str | None = None  # smallest hook of the usual range, e.g. "20"
    hook_size_max: str | None = None  # largest hook of the usual range, e.g. "10"
    colors: tuple[str, ...] = ()
    materials: tuple[Material, ...] = ()
    variants: tuple[Variant, ...] = ()
    habitats: tuple[Habitat, ...] = ()
    fishing_environments: tuple[FishingEnvironment, ...] = ()
    difficulty: Literal["beginner", "intermediate", "advanced"] | None = None
    texts: tuple[LocalizedText, ...] = ()
    data_source: str = "curated"
    verification_status: VerificationStatus = VerificationStatus.unverified
    is_demo: bool = False

    @model_validator(mode="after")
    def _check_hooks(self) -> FlyRecord:
        if self.hook_size_min and self.hook_size_max:
            if hook_size_index(self.hook_size_min) > hook_size_index(self.hook_size_max):
                raise ValueError(f"{self.slug}: hook_size_min must be the smaller hook")
        elif self.hook_size_min or self.hook_size_max:
            hook_size_index(self.hook_size_min or self.hook_size_max or "")
        return self


class MatchRecord(Record):
    id: uuid.UUID
    organism_id: uuid.UUID
    fly_pattern_id: uuid.UUID
    life_stage: LifeStage
    match_type: MatchType
    biological_compatibility: BiologicalCompatibility
    expert_verified: bool = False
    verification_source: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def _check(self) -> MatchRecord:
        if self.expert_verified and not self.verification_source:
            raise ValueError("expert_verified relations must name a verification_source")
        return self


class ImageRecord(Record):
    id: uuid.UUID
    owner_kind: Literal["organism", "fly"]
    owner_id: uuid.UUID
    image_url: str | None = None
    storage_path: str | None = None
    source: str = Field(min_length=1)
    source_id: str | None = None
    source_url: str | None = None
    license: str = Field(min_length=1)
    attribution: str = Field(min_length=1)
    commercial_use_allowed: bool
    permission_status: PermissionStatus
    image_view: str | None = None  # dorsal, lateral, ventral, top, side, macro...
    life_stage: LifeStage | None = None
    embedding_model: str | None = None

    @model_validator(mode="after")
    def _check(self) -> ImageRecord:
        if not self.image_url and not self.storage_path:
            raise ValueError("image needs image_url or storage_path")
        return self


class StoreRecord(Record):
    id: uuid.UUID
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    name: str
    website: HttpUrl
    country: str = Field(pattern=r"^[A-Z]{2}$")
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    description: str | None = None
    affiliate_program: bool = False
    shipping_countries: tuple[str, ...] = ()
    active: bool = True
    is_demo: bool = False

    @field_validator("shipping_countries")
    @classmethod
    def _iso(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        for value in values:
            if not re.fullmatch(r"[A-Z]{2}|WORLDWIDE", value):
                raise ValueError(f"invalid shipping country {value!r} (ISO 3166-1 alpha-2 or WORLDWIDE)")
        return values


class ProductRecord(Record):
    id: uuid.UUID
    store_id: uuid.UUID
    external_id: str = Field(min_length=1)  # store SKU or product handle
    name: str
    brand: str | None = None
    description: str | None = None
    product_url: HttpUrl
    affiliate_url: HttpUrl | None = None
    price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    availability_status: AvailabilityStatus = AvailabilityStatus.unknown
    country: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")
    last_verified_at: datetime | None = None
    active: bool = True
    is_demo: bool = False

    @model_validator(mode="after")
    def _check(self) -> ProductRecord:
        if self.price is not None and not self.currency:
            raise ValueError(f"{self.external_id}: price requires currency")
        if self.price is not None and self.last_verified_at is None:
            raise ValueError(f"{self.external_id}: a price must record last_verified_at")
        return self


class ProductPatternRecord(Record):
    id: uuid.UUID
    product_id: uuid.UUID
    fly_pattern_id: uuid.UUID
    size: str | None = None
    color: str | None = None
    variant: str | None = None


class CatalogDataset(BaseModel):
    """A complete, validated catalog (or a subset of one) ready to load or import."""

    organisms: list[OrganismRecord] = Field(default_factory=list)
    flies: list[FlyRecord] = Field(default_factory=list)
    matches: list[MatchRecord] = Field(default_factory=list)
    images: list[ImageRecord] = Field(default_factory=list)
    stores: list[StoreRecord] = Field(default_factory=list)
    products: list[ProductRecord] = Field(default_factory=list)
    product_patterns: list[ProductPatternRecord] = Field(default_factory=list)

    def merged(self, other: CatalogDataset) -> CatalogDataset:
        return CatalogDataset(
            organisms=self.organisms + other.organisms,
            flies=self.flies + other.flies,
            matches=self.matches + other.matches,
            images=self.images + other.images,
            stores=self.stores + other.stores,
            products=self.products + other.products,
            product_patterns=self.product_patterns + other.product_patterns,
        )
