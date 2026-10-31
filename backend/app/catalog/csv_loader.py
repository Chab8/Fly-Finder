"""Parse catalog CSV files into validated domain records.

Conventions (documented in docs/DATA_IMPORT.md):
- UTF-8, comma separated, header row required.
- Lines starting with '#' are comments and are ignored.
- Multi-valued cells use '|' as separator.
- Booleans: true/false (also yes/no, 1/0).
"""

from __future__ import annotations

import csv
import io
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.models.catalog import (
    CatalogDataset,
    CommonName,
    FlyRecord,
    ImageRecord,
    LocalizedText,
    MatchRecord,
    Material,
    OrganismRecord,
    ProductPatternRecord,
    ProductRecord,
    StoreRecord,
    Variant,
    stable_id,
)

LANGUAGES = ("en", "es")

FILES = {
    "organisms": "organisms.csv",
    "flies": "fly_patterns.csv",
    "matches": "fly_organism_matches.csv",
    "organism_images": "organism_images.csv",
    "fly_images": "fly_images.csv",
    "stores": "stores.csv",
    "products": "products.csv",
}


@dataclass
class Issue:
    file: str
    line: int | None
    message: str
    severity: str = "error"  # error | warning

    def __str__(self) -> str:
        where = f"{self.file}:{self.line}" if self.line else self.file
        return f"[{self.severity.upper()}] {where} {self.message}"


@dataclass
class LoadResult:
    dataset: CatalogDataset = field(default_factory=CatalogDataset)
    issues: list[Issue] = field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "error"]


def _split(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split("|") if part.strip()]


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None or value.strip() == "":
        return default
    normalized = value.strip().lower()
    if normalized in {"true", "yes", "1", "y"}:
        return True
    if normalized in {"false", "no", "0", "n"}:
        return False
    raise ValueError(f"invalid boolean {value!r}")


def _opt(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


def _rows(path: Path) -> Iterator[tuple[int, dict[str, str]]]:
    """Yield (line_number, row) skipping '#' comment lines and blank lines."""
    text = path.read_text(encoding="utf-8-sig")
    numbered = [(n, line) for n, line in enumerate(text.splitlines(), start=1) if line.strip() and not line.lstrip().startswith("#")]
    if not numbered:
        return
    reader = csv.DictReader(io.StringIO("\n".join(line for _, line in numbered)))
    for index, row in enumerate(reader, start=1):
        # DictReader consumed the header at numbered[0]; quoted multi-line cells are not supported.
        line_no = numbered[index][0] if index < len(numbered) else None
        yield line_no or 0, {k.strip(): (v or "").strip() for k, v in row.items() if k}


def _texts(row: dict[str, str], description_key: str, notes_key: str) -> tuple[LocalizedText, ...]:
    texts = []
    for lang in LANGUAGES:
        description = _opt(row.get(f"{description_key}_{lang}"))
        notes = _opt(row.get(f"{notes_key}_{lang}"))
        if description or notes:
            texts.append(LocalizedText(language=lang, description=description, fishing_notes=notes))
    return tuple(texts)


def _common_names(row: dict[str, str]) -> tuple[CommonName, ...]:
    names = []
    for lang in LANGUAGES:
        for position, name in enumerate(_split(row.get(f"common_names_{lang}"))):
            names.append(CommonName(language=lang, name=name, is_primary=position == 0))
    return tuple(names)


def parse_organism(row: dict[str, str]) -> OrganismRecord:
    return OrganismRecord(
        id=stable_id("organism", row["scientific_name"]),
        scientific_name=row["scientific_name"],
        taxonomic_rank=row["taxonomic_rank"],
        kingdom=_opt(row.get("kingdom")),
        phylum=_opt(row.get("phylum")),
        **{"class": _opt(row.get("class"))},
        order=_opt(row.get("order")),
        family=_opt(row.get("family")),
        genus=_opt(row.get("genus")),
        species=_opt(row.get("species")),
        gbif_taxon_id=_opt(row.get("gbif_taxon_id")),
        inaturalist_taxon_id=_opt(row.get("inaturalist_taxon_id")),
        organism_group=row["organism_group"],
        habitats=_split(row.get("habitats")),
        life_stages=_split(row.get("life_stages")),
        size_min=_opt(row.get("size_min")),
        size_max=_opt(row.get("size_max")),
        size_unit=_opt(row.get("size_unit")),
        geographic_distribution=_opt(row.get("geographic_distribution")),
        common_names=_common_names(row),
        texts=_texts(row, "description", "fishing_notes"),
        synonyms=_split(row.get("synonyms")),
        data_source=_opt(row.get("data_source")) or "curated",
        verification_status=_opt(row.get("verification_status")) or "unverified",
        is_demo=_bool(row.get("is_demo")),
    )


def _materials(value: str | None) -> tuple[Material, ...]:
    materials = []
    for item in _split(value):
        component, sep, material = item.partition(":")
        if not sep:
            raise ValueError(f"material {item!r} must be 'component:material'")
        materials.append(Material(component=component.strip(), material=material.strip()))
    return tuple(materials)


def parse_fly(row: dict[str, str]) -> FlyRecord:
    return FlyRecord(
        id=stable_id("fly", row["slug"]),
        slug=row["slug"],
        name=row["name"],
        alternate_names=_split(row.get("alternate_names")),
        category=row["category"],
        imitation_type=_opt(row.get("imitation_type")) or "not_specified",
        hook_size_min=_opt(row.get("hook_size_min")),
        hook_size_max=_opt(row.get("hook_size_max")),
        colors=_split(row.get("colors")),
        materials=_materials(row.get("materials")),
        variants=tuple(Variant(name=v) for v in _split(row.get("variants"))),
        habitats=_split(row.get("habitats")),
        fishing_environments=_split(row.get("fishing_environments")),
        difficulty=_opt(row.get("difficulty")),
        texts=_texts(row, "description", "usage_notes"),
        data_source=_opt(row.get("data_source")) or "curated",
        verification_status=_opt(row.get("verification_status")) or "unverified",
        is_demo=_bool(row.get("is_demo")),
    )


def parse_match(row: dict[str, str]) -> MatchRecord:
    organism_id = stable_id("organism", row["organism_scientific_name"])
    fly_id = stable_id("fly", row["fly_slug"])
    return MatchRecord(
        id=stable_id("match", row["organism_scientific_name"], row["fly_slug"], row["life_stage"]),
        organism_id=organism_id,
        fly_pattern_id=fly_id,
        life_stage=row["life_stage"],
        match_type=row["match_type"],
        biological_compatibility=row["biological_compatibility"],
        expert_verified=_bool(row.get("expert_verified")),
        verification_source=_opt(row.get("verification_source")),
        notes=_opt(row.get("notes")),
    )


def _image_parser(owner_kind: str) -> Callable[[dict[str, str]], ImageRecord]:
    def parse(row: dict[str, str]) -> ImageRecord:
        owner_key = row["owner_key"]
        locator = row.get("source_id") or row.get("image_url") or row.get("storage_path") or ""
        return ImageRecord(
            id=stable_id(f"{owner_kind}_image", owner_key, row["source"], locator),
            owner_kind=owner_kind,
            owner_id=stable_id(owner_kind, owner_key),
            image_url=_opt(row.get("image_url")),
            storage_path=_opt(row.get("storage_path")),
            source=row["source"],
            source_id=_opt(row.get("source_id")),
            source_url=_opt(row.get("source_url")),
            license=row["license"],
            attribution=row["attribution"],
            commercial_use_allowed=_bool(row.get("commercial_use_allowed")),
            permission_status=row["permission_status"],
            image_view=_opt(row.get("image_view")),
            life_stage=_opt(row.get("life_stage")),
        )

    return parse


def parse_store(row: dict[str, str]) -> StoreRecord:
    return StoreRecord(
        id=stable_id("store", row["slug"]),
        slug=row["slug"],
        name=row["name"],
        website=row["website"],
        country=row["country"],
        currency=row["currency"],
        description=_opt(row.get("description")),
        affiliate_program=_bool(row.get("affiliate_program")),
        shipping_countries=_split(row.get("shipping_countries")),
        active=_bool(row.get("active"), default=True),
        is_demo=_bool(row.get("is_demo")),
    )


def parse_product_row(row: dict[str, str]) -> tuple[ProductRecord, ProductPatternRecord | None]:
    product_id = stable_id("product", row["store_slug"], row["external_id"])
    verified = _opt(row.get("last_verified_at"))
    product = ProductRecord(
        id=product_id,
        store_id=stable_id("store", row["store_slug"]),
        external_id=row["external_id"],
        name=row["name"],
        brand=_opt(row.get("brand")),
        description=_opt(row.get("description")),
        product_url=row["product_url"],
        affiliate_url=_opt(row.get("affiliate_url")),
        price=_opt(row.get("price")),
        currency=_opt(row.get("currency")),
        availability_status=_opt(row.get("availability_status")) or "unknown",
        country=_opt(row.get("country")),
        last_verified_at=datetime.fromisoformat(verified) if verified else None,
        active=_bool(row.get("active"), default=True),
        is_demo=_bool(row.get("is_demo")),
    )
    link = None
    if _opt(row.get("fly_slug")):
        link = ProductPatternRecord(
            id=stable_id("product_pattern", row["store_slug"], row["external_id"], row["fly_slug"], row.get("size", ""), row.get("color", "")),
            product_id=product_id,
            fly_pattern_id=stable_id("fly", row["fly_slug"]),
            size=_opt(row.get("size")),
            color=_opt(row.get("color")),
            variant=_opt(row.get("variant")),
        )
    return product, link


def _load_file(path: Path, parser: Callable[[dict[str, str]], Any], result: LoadResult) -> list[Any]:
    records = []
    if not path.exists():
        return records
    for line_no, row in _rows(path):
        try:
            records.append(parser(row))
        except KeyError as exc:
            result.issues.append(Issue(path.name, line_no, f"missing required column {exc}"))
        except (ValidationError, ValueError) as exc:
            message = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors()) if isinstance(exc, ValidationError) else str(exc)
            result.issues.append(Issue(path.name, line_no, message))
    return records


def load_catalog_dir(directory: Path) -> LoadResult:
    """Load every known catalog CSV present in `directory` (missing files are allowed)."""
    result = LoadResult()
    dataset = result.dataset
    dataset.organisms = _load_file(directory / FILES["organisms"], parse_organism, result)
    dataset.flies = _load_file(directory / FILES["flies"], parse_fly, result)
    dataset.matches = _load_file(directory / FILES["matches"], parse_match, result)
    dataset.images = _load_file(directory / FILES["organism_images"], _image_parser("organism"), result) + _load_file(
        directory / FILES["fly_images"], _image_parser("fly"), result
    )
    dataset.stores = _load_file(directory / FILES["stores"], parse_store, result)
    products: dict = {}
    for product, link in _load_file(directory / FILES["products"], parse_product_row, result):
        products.setdefault(product.id, product)
        if link:
            dataset.product_patterns.append(link)
    dataset.products = list(products.values())
    return result
