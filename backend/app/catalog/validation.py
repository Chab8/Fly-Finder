"""Cross-record validation: duplicates, broken references and data-quality warnings."""

from __future__ import annotations

from collections import Counter
from difflib import SequenceMatcher

from app.catalog.csv_loader import Issue
from app.models.catalog import CatalogDataset
from app.models.enums import LifeStage, PermissionStatus

_FUZZY_DUPLICATE_RATIO = 0.92


def _normalize(name: str) -> str:
    return " ".join(name.lower().replace("'", "").replace("-", " ").split())


def _duplicates(values: list[str]) -> list[str]:
    return [value for value, count in Counter(values).items() if count > 1]


def validate_dataset(dataset: CatalogDataset) -> list[Issue]:
    issues: list[Issue] = []
    organism_ids = {o.id for o in dataset.organisms}
    fly_ids = {f.id for f in dataset.flies}
    store_ids = {s.id for s in dataset.stores}
    product_ids = {p.id for p in dataset.products}
    organisms_by_id = {o.id: o for o in dataset.organisms}

    for name in _duplicates([_normalize(o.scientific_name) for o in dataset.organisms]):
        issues.append(Issue("organisms.csv", None, f"duplicate scientific_name: {name}"))
    for slug in _duplicates([f.slug for f in dataset.flies]):
        issues.append(Issue("fly_patterns.csv", None, f"duplicate slug: {slug}"))

    # A name or alternate name must point to a single pattern, or search becomes ambiguous.
    owners: dict[str, set[str]] = {}
    for fly in dataset.flies:
        for name in (fly.name, *fly.alternate_names):
            owners.setdefault(_normalize(name), set()).add(fly.slug)
    for name, slugs in owners.items():
        if len(slugs) > 1:
            issues.append(Issue("fly_patterns.csv", None, f"name '{name}' used by several patterns: {sorted(slugs)}"))

    names = sorted({_normalize(f.name) for f in dataset.flies})
    for i, first in enumerate(names):
        for second in names[i + 1 :]:
            if SequenceMatcher(None, first, second).ratio() >= _FUZZY_DUPLICATE_RATIO:
                issues.append(Issue("fly_patterns.csv", None, f"possible duplicate patterns: '{first}' / '{second}'", "warning"))

    for o in dataset.organisms:
        if not o.common_names:
            issues.append(Issue("organisms.csv", None, f"{o.scientific_name}: no common names", "warning"))
        if o.gbif_taxon_id is None and not o.is_demo:
            issues.append(Issue("organisms.csv", None, f"{o.scientific_name}: missing gbif_taxon_id (run scripts/enrich_taxonomy.py)", "warning"))

    seen_matches = Counter((m.organism_id, m.fly_pattern_id, m.life_stage) for m in dataset.matches)
    for key, count in seen_matches.items():
        if count > 1:
            issues.append(Issue("fly_organism_matches.csv", None, f"duplicate relation {key}"))
    for match in dataset.matches:
        if match.organism_id not in organism_ids:
            issues.append(Issue("fly_organism_matches.csv", None, f"unknown organism for relation {match.id}"))
            continue
        if match.fly_pattern_id not in fly_ids:
            issues.append(Issue("fly_organism_matches.csv", None, f"unknown fly pattern for relation {match.id}"))
            continue
        organism = organisms_by_id[match.organism_id]
        if organism.life_stages and match.life_stage not in organism.life_stages and match.life_stage != LifeStage.unknown:
            issues.append(
                Issue(
                    "fly_organism_matches.csv",
                    None,
                    f"{organism.scientific_name}: relation uses life stage '{match.life_stage.value}' not listed for the organism",
                    "warning",
                )
            )

    for image in dataset.images:
        owners_ok = organism_ids if image.owner_kind == "organism" else fly_ids
        if image.owner_id not in owners_ok:
            issues.append(Issue(f"{image.owner_kind}_images.csv", None, f"image {image.source_id or image.image_url} has unknown owner"))
        if image.permission_status == PermissionStatus.approved and not image.commercial_use_allowed:
            issues.append(
                Issue(f"{image.owner_kind}_images.csv", None, f"image {image.source_id or image.image_url} approved but not cleared for commercial use", "warning")
            )

    for product in dataset.products:
        if product.store_id not in store_ids:
            issues.append(Issue("products.csv", None, f"product {product.external_id}: unknown store"))
    for link in dataset.product_patterns:
        if link.product_id not in product_ids:
            issues.append(Issue("products.csv", None, f"pattern link {link.id}: unknown product"))
        if link.fly_pattern_id not in fly_ids:
            issues.append(Issue("products.csv", None, f"pattern link {link.id}: unknown fly pattern"))

    real = [o for o in dataset.organisms if not o.is_demo] + [f for f in dataset.flies if not f.is_demo]
    if any(r.is_demo for r in dataset.organisms + dataset.flies) and real:
        issues.append(Issue("dataset", None, "demo and real records mixed in one dataset", "warning"))
    return issues
