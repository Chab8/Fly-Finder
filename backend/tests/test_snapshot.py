import uuid

import pytest

from app.core.errors import NotFoundError
from app.models.catalog import CatalogDataset, ImageRecord
from app.models.enums import FlyCategory, OrganismGroup
from app.repositories.catalog_snapshot import CatalogSnapshot, SnapshotProvider, normalize_name


def test_normalize_name_strips_accents_and_punctuation():
    assert normalize_name("  Hare's   Ear ") == "hare s ear"
    assert normalize_name("Efímeras") == "efimeras"


@pytest.mark.parametrize(
    ("query", "slug", "kind"),
    [("Adams", "adams", "exact"), ("PT Nymph", "pheasant-tail-nymph", "alternate_name"), ("Pheasant Tail Nimph", "pheasant-tail-nymph", "fuzzy")],
)
def test_find_fly_by_name(snapshot, query, slug, kind):
    fly, match = snapshot.find_fly_by_name(query)
    assert (fly.slug, match) == (slug, kind)


def test_unknown_fly_name_is_not_forced_onto_a_pattern(snapshot):
    assert snapshot.find_fly_by_name("Completely Unknown Bug") is None
    assert snapshot.find_fly_by_name("") is None


def test_resolve_lineage_most_specific_first(snapshot):
    lineage = snapshot.resolve_lineage(["Baetis rhodani", "Baetis", "Baetidae", "Ephemeroptera"])
    assert [o.scientific_name for o in lineage] == ["Baetis", "Baetidae", "Ephemeroptera"]


def test_list_filters_and_pagination(snapshot):
    crustaceans = snapshot.list_organisms(lang="en", group=OrganismGroup.crustacean, limit=3)
    assert crustaceans.total >= 5 and len(crustaceans.items) == 3
    assert all(o.organism_group == OrganismGroup.crustacean for o in crustaceans.items)
    saltwater = snapshot.list_flies(category=FlyCategory.saltwater)
    assert {"crazy-charlie", "merkin-crab"} <= {f.slug for f in saltwater.items}


def test_search_matches_common_names_in_spanish(snapshot):
    results = snapshot.search("sanguijuela", "es")
    assert [o.scientific_name for o in results.organisms] == ["Hirudinea"]


def test_localized_texts_with_fallback(snapshot):
    baetidae = snapshot.find_organism_by_name("Baetidae")
    es = snapshot.organism_detail(baetidae, "es")
    assert es.text_language == "es" and es.common_name == "Efímeras pequeñas"
    fallback = snapshot.organism_detail(baetidae, "fr")
    assert fallback.text_language == "en"


def test_fly_detail_includes_relations_and_materials(snapshot):
    fly = next(f for f in snapshot.flies.values() if f.slug == "pheasant-tail-nymph")
    detail = snapshot.fly_detail(fly, "en")
    assert detail.materials and detail.variants
    assert {"Baetidae", "Baetis"} <= {r.organism.scientific_name for r in detail.imitates}
    assert all(r.expert_verified is False for r in detail.imitates)


def test_attractor_has_no_forced_biological_relation(snapshot):
    royal_wulff = next(f for f in snapshot.flies.values() if f.slug == "royal-wulff")
    assert snapshot.fly_detail(royal_wulff, "en").imitates == []


def test_only_approved_images_are_exposed(catalog_dataset):
    organism = catalog_dataset.organisms[0]
    images = [
        ImageRecord(id=uuid.uuid4(), owner_kind="organism", owner_id=organism.id, image_url=f"https://img/{s}.jpg", source="own_photo",
                    license="CC BY 4.0", attribution="me", commercial_use_allowed=True, permission_status=s)
        for s in ("approved", "pending", "rejected")
    ]
    snapshot = CatalogSnapshot(catalog_dataset.model_copy(update={"images": images}), lambda i: i.image_url)
    detail = snapshot.organism_detail(organism, "en")
    assert [i.url for i in detail.images] == ["https://img/approved.jpg"]
    assert detail.thumbnail_url == "https://img/approved.jpg"


def test_get_missing_raises_not_found(snapshot):
    with pytest.raises(NotFoundError):
        snapshot.get_fly(uuid.uuid4())


def test_snapshot_provider_refreshes_and_survives_failed_refresh():
    calls = {"n": 0}
    now = {"t": 0.0}

    def loader():
        calls["n"] += 1
        if calls["n"] == 3:
            raise RuntimeError("db down")
        return CatalogSnapshot(CatalogDataset(), lambda i: None)

    provider = SnapshotProvider(loader, ttl_seconds=10, clock=lambda: now["t"])
    first = provider.get()
    now["t"] = 11
    second = provider.get()
    assert second is not first and calls["n"] == 2
    now["t"] = 30
    assert provider.get() is second  # refresh failed: previous snapshot is kept
