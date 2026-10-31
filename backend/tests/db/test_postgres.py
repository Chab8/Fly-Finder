"""Integration tests against a real PostgreSQL + pgvector with the Supabase migrations applied."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import numpy as np
import psycopg
import pytest
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

from app.api.deps import load_csv_dataset
from app.catalog.csv_loader import load_catalog_dir
from app.core.config import Settings
from app.repositories.identification_store import CandidateRow, IdentificationRecord
from app.repositories.postgres import (
    PgCatalogLoader,
    PgCatalogWriter,
    PgEmbeddingStore,
    PgIdentificationStore,
    PgVectorIndex,
    create_pool,
)
from tests.conftest import DEMO_DIR, TEMPLATES_DIR

pytestmark = pytest.mark.db


@pytest.fixture(scope="module")
def dataset():
    real = load_csv_dataset(Settings(_env_file=None))
    templates = load_catalog_dir(TEMPLATES_DIR).dataset  # includes images, a store and a priced product
    return real.merged(templates).merged(load_catalog_dir(DEMO_DIR).dataset)


@pytest.fixture(scope="module")
def pool(pg_url, dataset):
    with psycopg.connect(pg_url, row_factory=dict_row) as conn:
        conn.execute("set search_path = public, extensions")
        with conn.transaction():
            PgCatalogWriter(conn).write(dataset)
    pool = create_pool(pg_url)
    yield pool
    pool.close()


def connect(pg_url):
    conn = psycopg.connect(pg_url, row_factory=dict_row)
    conn.execute("set search_path = public, extensions")
    register_vector(conn)
    return conn


def test_roundtrip_preserves_catalog(pool, dataset):
    loaded = PgCatalogLoader(pool).load()
    assert len(loaded.organisms) == len(dataset.organisms)
    assert len(loaded.flies) == len(dataset.flies)
    assert len(loaded.matches) == len(dataset.matches)
    assert len(loaded.products) == len(dataset.products) and len(loaded.images) == len(dataset.images)
    original = {o.id: o for o in dataset.organisms}
    for organism in loaded.organisms:
        source = original[organism.id]
        assert organism.scientific_name == source.scientific_name
        assert set(organism.life_stages) == set(source.life_stages)
        assert {(n.language, n.name, n.is_primary) for n in organism.common_names} == {(n.language, n.name, n.is_primary) for n in source.common_names}
        assert organism.gbif_taxon_id == source.gbif_taxon_id
    adams = next(f for f in loaded.flies if f.slug == "adams")
    assert [m.component for m in adams.materials][:2] == ["hook", "thread"]


def test_reimport_is_idempotent(pg_url, pool, dataset):
    with connect(pg_url) as conn:
        before = conn.execute("select (select count(*) from organisms) o, (select count(*) from common_names) c, (select count(*) from fly_organism_matches) m").fetchone()
        with conn.transaction():
            PgCatalogWriter(conn).write(dataset)
        after = conn.execute("select (select count(*) from organisms) o, (select count(*) from common_names) c, (select count(*) from fly_organism_matches) m").fetchone()
    assert before == after


def test_reimport_without_upload_keeps_storage_path(pg_url, pool, dataset):
    image = next(i for i in dataset.images if i.owner_kind == "organism")
    with connect(pg_url) as conn:
        with conn.transaction():
            PgCatalogWriter(conn).upsert_images([image.model_copy(update={"storage_path": "organism/x/y.jpg"})])
        with conn.transaction():
            PgCatalogWriter(conn).upsert_images([image.model_copy(update={"storage_path": None})])
        stored = conn.execute("select storage_path from organism_images where id = %s", (image.id,)).fetchone()
        with conn.transaction():
            conn.execute("update organism_images set storage_path = %s where id = %s", (image.storage_path, image.id))
    assert stored["storage_path"] == "organism/x/y.jpg"


def test_constraints_reject_invalid_data(pg_url, pool):
    with connect(pg_url) as conn:
        for sql in [
            "insert into organisms (scientific_name, taxonomic_rank, organism_group) values ('Baetis', 'genus', 'aquatic_insect')",  # duplicate (case-insensitive)
            "insert into organisms (scientific_name, taxonomic_rank, organism_group) values ('Baetisx', 'species', 'aquatic_insect')",  # species without binomial
            "insert into products (store_id, external_id, name, product_url, price) select id, 'zz', 'x', 'https://x', 10 from stores limit 1",  # price w/o currency
        ]:
            with pytest.raises(psycopg.errors.IntegrityError):
                with conn.transaction():
                    conn.execute(sql)


def test_vector_search_and_embedding_store(pg_url, pool):
    model = "open_clip:ViT-B-32:laion2b_s34b_b79k"
    with connect(pg_url) as conn:
        conn.execute("update fly_images set permission_status = 'approved'")
        conn.commit()
        store = PgEmbeddingStore(conn)
        pending = store.images_missing_embedding("fly", model, 10)
        assert pending
        vector = np.zeros(512, dtype=np.float32)
        vector[0] = 1
        store.save_embedding("fly", pending[0]["id"], model, vector)
        conn.commit()
        assert pending[0]["id"] not in {row["id"] for row in store.images_missing_embedding("fly", model, 1000)}
    hits = PgVectorIndex(pool).search("fly", vector, model, k=5)
    assert len(hits) == 1 and hits[0].similarity == pytest.approx(1.0)
    assert PgVectorIndex(pool).search("fly", vector, "other:model", k=5) == []


def test_identification_store(pool):
    store = PgIdentificationStore(pool)
    record = IdentificationRecord(
        id=uuid.uuid4(), client_hash="abc", kind="fly", match_level="low_match", primary_label="Adams", result={"x": 1},
        analysis_source="gemini", ai_model="m", embedding_model=None, created_at=datetime.now(UTC),
        candidates=[CandidateRow(position=1, label="Adams")],
    )
    store.save(record)
    assert [r.id for r in store.list_for_client("abc", 10)] == [record.id]
    assert store.get_for_client(record.id, "abc").result == {"x": 1}
    assert store.get_for_client(record.id, "someone-else") is None


def test_row_level_security_for_anon(pg_url, pool):
    with connect(pg_url) as conn:
        conn.execute("update organism_images set permission_status = 'pending'")
        conn.commit()
        conn.execute("set role anon")
        assert conn.execute("select count(*) n from organisms").fetchone()["n"] > 0
        assert conn.execute("select count(*) n from organism_images").fetchone()["n"] == 0  # pending images hidden
        assert conn.execute("select count(*) n from identifications").fetchone()["n"] == 0
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute("insert into stores (slug, name, website, country, currency) values ('x', 'x', 'https://x', 'AR', 'ARS')")
