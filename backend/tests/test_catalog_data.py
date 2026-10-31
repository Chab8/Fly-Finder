"""The curated catalog, the demo data and the templates must always load cleanly."""

from pathlib import Path

import pytest

from app.catalog.csv_loader import load_catalog_dir
from app.catalog.validation import validate_dataset
from app.models.catalog import stable_id
from app.models.enums import VerificationStatus
from tests.conftest import CATALOG_DIR, DEMO_DIR, TEMPLATES_DIR


@pytest.mark.parametrize("directory", [CATALOG_DIR, DEMO_DIR, TEMPLATES_DIR])
def test_dataset_loads_without_errors(directory):
    result = load_catalog_dir(directory)
    errors = result.errors + [i for i in validate_dataset(result.dataset) if i.severity == "error"]
    assert errors == [], "\n".join(map(str, errors))


def test_curated_catalog_has_no_demo_records_and_no_invented_commerce():
    dataset = load_catalog_dir(CATALOG_DIR).dataset
    assert len(dataset.organisms) >= 30 and len(dataset.flies) >= 50
    assert not any(o.is_demo for o in dataset.organisms) and not any(f.is_demo for f in dataset.flies)
    assert dataset.stores == [] and dataset.products == []  # no real shop data yet: never invent it
    assert not any(m.expert_verified for m in dataset.matches)  # nothing is expert-reviewed yet


def test_source_verified_organisms_have_gbif_ids():
    dataset = load_catalog_dir(CATALOG_DIR).dataset
    for organism in dataset.organisms:
        if organism.verification_status == VerificationStatus.source_verified:
            assert organism.gbif_taxon_id, organism.scientific_name


def test_demo_records_are_all_flagged():
    dataset = load_catalog_dir(DEMO_DIR).dataset
    assert all(o.is_demo for o in dataset.organisms) and all(f.is_demo for f in dataset.flies)
    assert all(p.price is None for p in dataset.products)


def test_ids_are_deterministic():
    assert stable_id("fly", "adams") == stable_id("fly", " Adams ")
    assert stable_id("fly", "adams") != stable_id("organism", "adams")


def _write(tmp_path: Path, name: str, content: str) -> None:
    (tmp_path / name).write_text(content, encoding="utf-8")


ORG_HEADER = "scientific_name,taxonomic_rank,order,family,organism_group,life_stages,common_names_en\n"
FLY_HEADER = "slug,name,category,alternate_names,hook_size_min,hook_size_max\n"


def test_validation_catches_bad_rows(tmp_path):
    _write(tmp_path, "organisms.csv", ORG_HEADER + "Baetidae,family,Ephemeroptera,Baetidae,aquatic_insect,nymph,Mayfly\nBaetis,species,,,aquatic_insect,,X\n")
    _write(tmp_path, "fly_patterns.csv", FLY_HEADER + "adams,Adams,dry_fly,,10,20\npt,PT,nymph,Adams,,\n")
    _write(
        tmp_path, "fly_organism_matches.csv",
        "organism_scientific_name,fly_slug,life_stage,match_type,biological_compatibility,expert_verified,verification_source\n"
        "Baetidae,unknown-fly,nymph,general_imitation,high,false,\n"
        "Baetidae,pt,nymph,general_imitation,high,true,\n",
    )
    result = load_catalog_dir(tmp_path)
    messages = [str(i) for i in result.issues + validate_dataset(result.dataset)]
    joined = "\n".join(messages)
    assert "species rank requires a binomial" in joined          # invented species-level name
    assert "hook_size_min must be the smaller hook" in joined      # 10 is bigger than 20
    assert "expert_verified relations must name a verification_source" in joined
    assert "unknown fly pattern" in joined


def test_duplicate_names_are_detected(tmp_path):
    _write(tmp_path, "fly_patterns.csv", FLY_HEADER + "adams,Adams,dry_fly,,,\nadams-2,Adams,dry_fly,,,\n")
    issues = validate_dataset(load_catalog_dir(tmp_path).dataset)
    assert any("used by several patterns" in str(i) for i in issues)


def test_price_requires_currency_and_verification_date(tmp_path):
    _write(tmp_path, "stores.csv", "slug,name,website,country,currency\nshop,Shop,https://example.com,AR,ARS\n")
    _write(
        tmp_path, "products.csv",
        "store_slug,external_id,name,product_url,price,currency,last_verified_at\nshop,1,X,https://example.com/x,10,ARS,\n",
    )
    result = load_catalog_dir(tmp_path)
    assert any("last_verified_at" in str(i) for i in result.errors)
