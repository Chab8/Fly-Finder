"""Indexed, read-only view of the catalog with query and presentation helpers.

The curated catalog is small (hundreds to low tens of thousands of records), so it is
held in memory and refreshed periodically. Vector search and identification logs are
NOT served from here; they use pgvector / Postgres directly (see vector_index.py).
"""

from __future__ import annotations

import threading
import time
import unicodedata
import uuid
from collections import defaultdict
from collections.abc import Callable, Iterable
from difflib import SequenceMatcher

from app.core.errors import NotFoundError
from app.models.catalog import (
    CatalogDataset,
    FlyRecord,
    ImageRecord,
    LocalizedText,
    MatchRecord,
    OrganismRecord,
    ProductRecord,
)
from app.models.enums import RANK_LEVEL, FishingEnvironment, FlyCategory, OrganismGroup, PermissionStatus, TaxonRank
from app.schemas.catalog import (
    FlyPatternDetail,
    FlyPatternSummary,
    ImageInfo,
    ImitatedOrganism,
    ImitatingFly,
    OrganismDetail,
    OrganismSummary,
    Page,
    SearchResults,
    Taxonomy,
)
from app.schemas.commerce import ProductInfo, ProductPatternLink, StoreInfo

DEFAULT_LANGUAGE = "en"
_FUZZY_NAME_CUTOFF = 0.86


def normalize_name(value: str) -> str:
    stripped = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    cleaned = "".join(ch if ch.isalnum() else " " for ch in stripped.lower())
    return " ".join(cleaned.split())


def _pick_text(texts: Iterable[LocalizedText], lang: str) -> LocalizedText | None:
    by_lang = {t.language: t for t in texts}
    return by_lang.get(lang) or by_lang.get(DEFAULT_LANGUAGE) or next(iter(by_lang.values()), None)


class CatalogSnapshot:
    def __init__(self, dataset: CatalogDataset, image_url: Callable[[ImageRecord], str | None]):
        self._image_url = image_url
        self.organisms: dict[uuid.UUID, OrganismRecord] = {o.id: o for o in dataset.organisms}
        self.flies: dict[uuid.UUID, FlyRecord] = {f.id: f for f in dataset.flies}
        self.stores = {s.id: s for s in dataset.stores if s.active}
        self.products = {p.id: p for p in dataset.products if p.active and p.store_id in self.stores}

        self._matches_by_organism: dict[uuid.UUID, list[MatchRecord]] = defaultdict(list)
        self._matches_by_fly: dict[uuid.UUID, list[MatchRecord]] = defaultdict(list)
        for match in dataset.matches:
            if match.organism_id in self.organisms and match.fly_pattern_id in self.flies:
                self._matches_by_organism[match.organism_id].append(match)
                self._matches_by_fly[match.fly_pattern_id].append(match)

        # Only images with explicit permission are ever shown to users.
        self._images: dict[uuid.UUID, list[ImageRecord]] = defaultdict(list)
        self.images_by_id: dict[uuid.UUID, ImageRecord] = {}
        for image in dataset.images:
            if image.permission_status == PermissionStatus.approved:
                self._images[image.owner_id].append(image)
                self.images_by_id[image.id] = image

        self._links_by_fly = defaultdict(list)
        self._links_by_product = defaultdict(list)
        for link in dataset.product_patterns:
            if link.product_id in self.products:
                self._links_by_fly[link.fly_pattern_id].append(link)
                self._links_by_product[link.product_id].append(link)

        self._organism_names: dict[str, OrganismRecord] = {}
        for organism in self.organisms.values():
            for name in (organism.scientific_name, *organism.synonyms):
                self._organism_names.setdefault(normalize_name(name), organism)

        self._fly_names: dict[str, tuple[FlyRecord, str]] = {}
        for fly in self.flies.values():
            self._fly_names[normalize_name(fly.name)] = (fly, "exact")
        for fly in self.flies.values():
            for alt in fly.alternate_names:
                self._fly_names.setdefault(normalize_name(alt), (fly, "alternate_name"))

    # ---------------------------------------------------------------- presenters
    def _image_infos(self, owner_id: uuid.UUID) -> list[ImageInfo]:
        infos = []
        for image in self._images.get(owner_id, []):
            url = self._image_url(image)
            if url:
                infos.append(
                    ImageInfo(
                        id=image.id, url=url, source=image.source, source_url=image.source_url, license=image.license,
                        attribution=image.attribution, image_view=image.image_view, life_stage=image.life_stage,
                    )
                )
        return infos

    def _thumbnail(self, owner_id: uuid.UUID) -> str | None:
        images = self._image_infos(owner_id)
        return images[0].url if images else None

    @staticmethod
    def common_name(organism: OrganismRecord, lang: str) -> str | None:
        for language in (lang, DEFAULT_LANGUAGE):
            names = [n for n in organism.common_names if n.language == language]
            if names:
                return next((n.name for n in names if n.is_primary), names[0].name)
        return None

    def organism_summary(self, organism: OrganismRecord, lang: str) -> OrganismSummary:
        return OrganismSummary(
            id=organism.id, scientific_name=organism.scientific_name, common_name=self.common_name(organism, lang),
            taxonomic_rank=organism.taxonomic_rank, order=organism.order, family=organism.family, genus=organism.genus,
            organism_group=organism.organism_group, thumbnail_url=self._thumbnail(organism.id), is_demo=organism.is_demo,
        )

    def fly_summary(self, fly: FlyRecord) -> FlyPatternSummary:
        return FlyPatternSummary(
            id=fly.id, slug=fly.slug, name=fly.name, category=fly.category, imitation_type=fly.imitation_type,
            hook_size_min=fly.hook_size_min, hook_size_max=fly.hook_size_max, colors=list(fly.colors),
            thumbnail_url=self._thumbnail(fly.id), is_demo=fly.is_demo,
        )

    @staticmethod
    def _relation_fields(match: MatchRecord) -> dict:
        return {
            "life_stage": match.life_stage, "match_type": match.match_type,
            "biological_compatibility": match.biological_compatibility, "expert_verified": match.expert_verified,
            "verification_source": match.verification_source, "notes": match.notes,
        }

    def imitated_organisms(self, fly_id: uuid.UUID, lang: str) -> list[ImitatedOrganism]:
        return [
            ImitatedOrganism(organism=self.organism_summary(self.organisms[m.organism_id], lang), **self._relation_fields(m))
            for m in self._matches_by_fly.get(fly_id, [])
        ]

    def organism_detail(self, organism: OrganismRecord, lang: str) -> OrganismDetail:
        text = _pick_text(organism.texts, lang)
        imitated_by = [
            ImitatingFly(fly=self.fly_summary(self.flies[m.fly_pattern_id]), **self._relation_fields(m))
            for m in self._matches_by_organism.get(organism.id, [])
        ]
        return OrganismDetail(
            **self.organism_summary(organism, lang).model_dump(),
            taxonomy=Taxonomy(
                kingdom=organism.kingdom, phylum=organism.phylum, class_name=organism.class_name, order=organism.order,
                family=organism.family, genus=organism.genus, species=organism.species,
            ),
            gbif_taxon_id=organism.gbif_taxon_id, inaturalist_taxon_id=organism.inaturalist_taxon_id,
            common_names=list(organism.common_names), synonyms=list(organism.synonyms), habitats=list(organism.habitats),
            life_stages=list(organism.life_stages), size_min=organism.size_min, size_max=organism.size_max,
            size_unit=organism.size_unit, geographic_distribution=organism.geographic_distribution,
            description=text.description if text else None, fishing_notes=text.fishing_notes if text else None,
            text_language=text.language if text else None, images=self._image_infos(organism.id),
            imitated_by=imitated_by, data_source=organism.data_source, verification_status=organism.verification_status,
        )

    def fly_detail(self, fly: FlyRecord, lang: str) -> FlyPatternDetail:
        text = _pick_text(fly.texts, lang)
        return FlyPatternDetail(
            **self.fly_summary(fly).model_dump(),
            alternate_names=list(fly.alternate_names), materials=list(fly.materials), variants=list(fly.variants),
            habitats=list(fly.habitats), fishing_environments=list(fly.fishing_environments), difficulty=fly.difficulty,
            description=text.description if text else None, usage_notes=text.fishing_notes if text else None,
            text_language=text.language if text else None, images=self._image_infos(fly.id),
            imitates=self.imitated_organisms(fly.id, lang), product_count=len(self.products_for_fly(fly.id)),
            data_source=fly.data_source, verification_status=fly.verification_status,
        )

    def store_info(self, store_id: uuid.UUID) -> StoreInfo:
        store = self.stores[store_id]
        return StoreInfo(
            id=store.id, slug=store.slug, name=store.name, website=str(store.website), country=store.country,
            currency=store.currency, description=store.description, affiliate_program=store.affiliate_program,
            shipping_countries=list(store.shipping_countries), is_demo=store.is_demo,
        )

    def product_info(self, product: ProductRecord, country: str | None) -> ProductInfo:
        store = self.stores[product.store_id]
        ships = None
        if country:
            ships = "WORLDWIDE" in store.shipping_countries or country.upper() in store.shipping_countries or store.country == country.upper()
        return ProductInfo(
            id=product.id, name=product.name, brand=product.brand, description=product.description,
            store=self.store_info(product.store_id), buy_url=str(product.affiliate_url or product.product_url),
            product_url=str(product.product_url), price=product.price, currency=product.currency,
            availability_status=product.availability_status, country=product.country,
            last_verified_at=product.last_verified_at,
            patterns=[
                ProductPatternLink(fly_pattern_id=link.fly_pattern_id, size=link.size, color=link.color, variant=link.variant)
                for link in self._links_by_product.get(product.id, [])
            ],
            ships_to_requested_country=ships, is_demo=product.is_demo,
        )

    # ------------------------------------------------------------------- queries
    def get_organism(self, organism_id: uuid.UUID) -> OrganismRecord:
        if organism_id not in self.organisms:
            raise NotFoundError("Organism not found")
        return self.organisms[organism_id]

    def get_fly(self, fly_id: uuid.UUID) -> FlyRecord:
        if fly_id not in self.flies:
            raise NotFoundError("Fly pattern not found")
        return self.flies[fly_id]

    def _organism_matches_query(self, organism: OrganismRecord, q: str) -> bool:
        haystack = [organism.scientific_name, *organism.synonyms, *(n.name for n in organism.common_names), organism.family or "", organism.order or ""]
        return any(q in normalize_name(value) for value in haystack)

    def list_organisms(
        self, *, lang: str, q: str | None = None, group: OrganismGroup | None = None, order: str | None = None,
        family: str | None = None, rank: TaxonRank | None = None, limit: int = 50, offset: int = 0,
    ) -> Page[OrganismSummary]:
        nq = normalize_name(q) if q else None
        items = [
            o for o in self.organisms.values()
            if (not nq or self._organism_matches_query(o, nq))
            and (not group or o.organism_group == group)
            and (not order or (o.order or "").lower() == order.lower())
            and (not family or (o.family or "").lower() == family.lower())
            and (not rank or o.taxonomic_rank == rank)
        ]
        items.sort(key=lambda o: (o.order or "", o.family or "", RANK_LEVEL[o.taxonomic_rank], o.scientific_name))
        page = items[offset : offset + limit]
        return Page[OrganismSummary](items=[self.organism_summary(o, lang) for o in page], total=len(items), limit=limit, offset=offset)

    def list_flies(
        self, *, q: str | None = None, category: FlyCategory | None = None, environment: FishingEnvironment | None = None,
        limit: int = 50, offset: int = 0,
    ) -> Page[FlyPatternSummary]:
        nq = normalize_name(q) if q else None
        items = [
            f for f in self.flies.values()
            if (not nq or any(nq in normalize_name(n) for n in (f.name, *f.alternate_names)))
            and (not category or f.category == category)
            and (not environment or environment in f.fishing_environments)
        ]
        items.sort(key=lambda f: f.name.lower())
        page = items[offset : offset + limit]
        return Page[FlyPatternSummary](items=[self.fly_summary(f) for f in page], total=len(items), limit=limit, offset=offset)

    def search(self, q: str, lang: str, limit: int = 20) -> SearchResults:
        organisms = self.list_organisms(lang=lang, q=q, limit=limit).items
        flies = self.list_flies(q=q, limit=limit).items
        return SearchResults(query=q, organisms=organisms, flies=flies)

    def find_organism_by_name(self, name: str) -> OrganismRecord | None:
        return self._organism_names.get(normalize_name(name))

    def resolve_lineage(self, names_specific_first: list[str]) -> list[OrganismRecord]:
        """Catalog organisms matching a taxon or any of its ancestors, most specific first."""
        found: list[OrganismRecord] = []
        for name in names_specific_first:
            organism = self.find_organism_by_name(name)
            if organism and organism not in found:
                found.append(organism)
        return found

    def find_fly_by_name(self, name: str) -> tuple[FlyRecord, str] | None:
        key = normalize_name(name)
        if not key:
            return None
        if key in self._fly_names:
            return self._fly_names[key]
        best, best_ratio = None, 0.0
        for candidate, (fly, _) in self._fly_names.items():
            ratio = SequenceMatcher(None, key, candidate).ratio()
            if ratio > best_ratio:
                best, best_ratio = fly, ratio
        return (best, "fuzzy") if best and best_ratio >= _FUZZY_NAME_CUTOFF else None

    def relations_for_organism(self, organism_id: uuid.UUID) -> list[MatchRecord]:
        return list(self._matches_by_organism.get(organism_id, []))

    def relations_for_fly(self, fly_id: uuid.UUID) -> list[MatchRecord]:
        return list(self._matches_by_fly.get(fly_id, []))

    def products_for_fly(self, fly_id: uuid.UUID) -> list[ProductRecord]:
        seen, products = set(), []
        for link in self._links_by_fly.get(fly_id, []):
            if link.product_id not in seen:
                seen.add(link.product_id)
                products.append(self.products[link.product_id])
        return products

    def all_products(self) -> list[ProductRecord]:
        return list(self.products.values())

    def fly_names(self) -> list[str]:
        return sorted(f.name for f in self.flies.values())


class SnapshotProvider:
    """Holds the current snapshot; reloads it after `ttl_seconds` (None = never)."""

    def __init__(self, loader: Callable[[], CatalogSnapshot], ttl_seconds: float | None = None, clock=time.monotonic):
        self._loader = loader
        self._ttl = ttl_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self._snapshot: CatalogSnapshot | None = None
        self._loaded_at = 0.0

    def get(self) -> CatalogSnapshot:
        expired = self._ttl is not None and self._clock() - self._loaded_at > self._ttl
        if self._snapshot is None or expired:
            with self._lock:
                if self._snapshot is None or (self._ttl is not None and self._clock() - self._loaded_at > self._ttl):
                    try:
                        self._snapshot = self._loader()
                        self._loaded_at = self._clock()
                    except Exception:
                        if self._snapshot is None:
                            raise
                        # Keep serving the previous snapshot if a refresh fails.
                        self._loaded_at = self._clock()
        return self._snapshot

    def refresh(self) -> None:
        with self._lock:
            self._snapshot = self._loader()
            self._loaded_at = self._clock()
