"""All SQL used by the backend lives in this module.

- PgCatalogLoader:       reads the catalog into domain records (feeds CatalogSnapshot)
- PgCatalogWriter:       idempotent upserts used by the import scripts
- PgVectorIndex:         pgvector similarity search over catalog images
- PgEmbeddingStore:      reads/writes image embeddings (generate_embeddings script)
- PgIdentificationStore: identification log
"""

from __future__ import annotations

import json
import uuid
from collections import defaultdict
from collections.abc import Sequence

import numpy as np
from pgvector.psycopg import register_vector
from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

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
)
from app.repositories.identification_store import IdentificationRecord
from app.repositories.vector_index import VectorHit, aggregate_by_owner

_IMAGE_TABLES = {"organism": ("organism_images", "organism_id"), "fly": ("fly_images", "fly_pattern_id")}


def _configure(conn: Connection) -> None:
    # Supabase installs extensions in the `extensions` schema.
    conn.execute("set search_path = public, extensions")
    conn.commit()
    register_vector(conn)


def create_pool(database_url: str, *, min_size: int = 1, max_size: int = 5) -> ConnectionPool:
    return ConnectionPool(
        database_url,
        min_size=min_size,
        max_size=max_size,
        configure=_configure,
        kwargs={"row_factory": dict_row, "connect_timeout": 10, "application_name": "fly-finder-backend"},
        open=True,
    )


def _texts(rows: list[dict], notes_key: str) -> tuple[LocalizedText, ...]:
    return tuple(LocalizedText(language=r["language"], description=r["description"], fishing_notes=r[notes_key]) for r in rows)


class PgCatalogLoader:
    def __init__(self, pool: ConnectionPool):
        self._pool = pool

    def load(self) -> CatalogDataset:
        with self._pool.connection() as conn:
            q = lambda sql: conn.execute(sql).fetchall()  # noqa: E731
            stages = {r["id"]: r["code"] for r in q("select id, code from life_stages")}

            organism_stages, names, org_texts, synonyms = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
            for r in q("select organism_id, life_stage_id from organism_life_stages"):
                organism_stages[r["organism_id"]].append(stages[r["life_stage_id"]])
            for r in q("select organism_id, language, name, is_primary from common_names order by is_primary desc, name"):
                names[r["organism_id"]].append(CommonName(language=r["language"], name=r["name"], is_primary=r["is_primary"]))
            for r in q("select organism_id, language, description, fishing_notes from organism_texts"):
                org_texts[r["organism_id"]].append(r)
            for r in q("select organism_id, synonym from taxonomic_synonyms order by synonym"):
                synonyms[r["organism_id"]].append(r["synonym"])

            organisms = [
                OrganismRecord(
                    id=r["id"], scientific_name=r["scientific_name"], taxonomic_rank=r["taxonomic_rank"],
                    kingdom=r["kingdom"], phylum=r["phylum"], **{"class": r["class"]}, order=r["order"],
                    family=r["family"], genus=r["genus"], species=r["species"], gbif_taxon_id=r["gbif_taxon_id"],
                    inaturalist_taxon_id=r["inaturalist_taxon_id"], organism_group=r["organism_group"],
                    habitats=r["habitats"], life_stages=organism_stages[r["id"]], size_min=r["size_min"],
                    size_max=r["size_max"], size_unit=r["size_unit"], geographic_distribution=r["geographic_distribution"],
                    common_names=names[r["id"]], texts=_texts(org_texts[r["id"]], "fishing_notes"),
                    synonyms=synonyms[r["id"]], data_source=r["data_source"],
                    verification_status=r["verification_status"], is_demo=r["is_demo"],
                )
                for r in q("select * from organisms")
            ]

            fly_texts, materials, variants = defaultdict(list), defaultdict(list), defaultdict(list)
            for r in q("select fly_pattern_id, language, description, usage_notes from fly_pattern_texts"):
                fly_texts[r["fly_pattern_id"]].append(r)
            for r in q("select fly_pattern_id, component, material from fly_pattern_materials order by sort_order"):
                materials[r["fly_pattern_id"]].append(Material(component=r["component"], material=r["material"]))
            for r in q("select fly_pattern_id, name, description from fly_pattern_variants order by name"):
                variants[r["fly_pattern_id"]].append(Variant(name=r["name"], description=r["description"]))

            flies = [
                FlyRecord(
                    id=r["id"], slug=r["slug"], name=r["name"], alternate_names=r["alternate_names"],
                    category=r["category"], imitation_type=r["imitation_type"], hook_size_min=r["hook_size_min"],
                    hook_size_max=r["hook_size_max"], colors=r["colors"], materials=materials[r["id"]],
                    variants=variants[r["id"]], habitats=r["habitats"], fishing_environments=r["fishing_environments"],
                    difficulty=r["difficulty"], texts=_texts(fly_texts[r["id"]], "usage_notes"),
                    data_source=r["data_source"], verification_status=r["verification_status"], is_demo=r["is_demo"],
                )
                for r in q("select * from fly_patterns")
            ]

            matches = [
                MatchRecord(
                    id=r["id"], organism_id=r["organism_id"], fly_pattern_id=r["fly_pattern_id"],
                    life_stage=stages[r["life_stage_id"]], match_type=r["match_type"],
                    biological_compatibility=r["biological_compatibility"], expert_verified=r["expert_verified"],
                    verification_source=r["verification_source"], notes=r["notes"],
                )
                for r in q("select * from fly_organism_matches")
            ]

            images = []
            for kind, (table, owner_col) in _IMAGE_TABLES.items():
                stage_col = "life_stage_id" if kind == "organism" else "null::uuid as life_stage_id"
                sql = (
                    f"select id, {owner_col} as owner_id, image_url, storage_path, source, source_id, source_url, license, "
                    f"attribution, commercial_use_allowed, permission_status, image_view, {stage_col}, embedding_model from {table}"
                )
                for r in q(sql):
                    images.append(ImageRecord(owner_kind=kind, life_stage=stages.get(r.pop("life_stage_id")), **r))

            stores = [StoreRecord(**r) for r in q(
                "select id, slug, name, website, country, currency, description, affiliate_program, shipping_countries, active, is_demo from stores"
            )]
            products = [ProductRecord(**r) for r in q(
                "select id, store_id, external_id, name, brand, description, product_url, affiliate_url, price, currency, "
                "availability_status, country, last_verified_at, active, is_demo from products"
            )]
            links = [ProductPatternRecord(**r) for r in q("select id, product_id, fly_pattern_id, size, color, variant from product_patterns")]

        return CatalogDataset(
            organisms=organisms, flies=flies, matches=matches, images=images, stores=stores, products=products,
            product_patterns=links,
        )


class PgCatalogWriter:
    """Idempotent upserts keyed on deterministic IDs.

    Child lists (common names, texts, stages, synonyms, materials, variants) of each
    imported record are replaced by the imported values. Embeddings are never touched.
    """

    def __init__(self, conn: Connection):
        self._conn = conn
        self._stages = {r["code"]: r["id"] for r in conn.execute("select id, code from life_stages").fetchall()}

    def _replace_children(self, table: str, key: str, owner_id: uuid.UUID, columns: Sequence[str], rows: Sequence[Sequence]) -> None:
        self._conn.execute(f"delete from {table} where {key} = %s", (owner_id,))
        if rows:
            placeholders = ", ".join(["%s"] * (len(columns) + 1))
            with self._conn.cursor() as cur:
                cur.executemany(
                    f"insert into {table} ({key}, {', '.join(columns)}) values ({placeholders})",
                    [(owner_id, *row) for row in rows],
                )

    def upsert_organisms(self, organisms: Sequence[OrganismRecord]) -> int:
        for o in organisms:
            self._conn.execute(
                """
                insert into organisms (id, scientific_name, taxonomic_rank, kingdom, phylum, "class", "order", family, genus,
                  species, gbif_taxon_id, inaturalist_taxon_id, organism_group, habitats, size_min, size_max, size_unit,
                  geographic_distribution, data_source, verification_status, is_demo)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                on conflict (id) do update set scientific_name = excluded.scientific_name,
                  taxonomic_rank = excluded.taxonomic_rank, kingdom = excluded.kingdom, phylum = excluded.phylum,
                  "class" = excluded."class", "order" = excluded."order", family = excluded.family, genus = excluded.genus,
                  species = excluded.species, gbif_taxon_id = excluded.gbif_taxon_id,
                  inaturalist_taxon_id = excluded.inaturalist_taxon_id, organism_group = excluded.organism_group,
                  habitats = excluded.habitats, size_min = excluded.size_min, size_max = excluded.size_max,
                  size_unit = excluded.size_unit, geographic_distribution = excluded.geographic_distribution,
                  data_source = excluded.data_source, verification_status = excluded.verification_status,
                  is_demo = excluded.is_demo
                """,
                (o.id, o.scientific_name, o.taxonomic_rank.value, o.kingdom, o.phylum, o.class_name, o.order, o.family,
                 o.genus, o.species, o.gbif_taxon_id, o.inaturalist_taxon_id, o.organism_group.value,
                 [h.value for h in o.habitats], o.size_min, o.size_max, o.size_unit, o.geographic_distribution,
                 o.data_source, o.verification_status.value, o.is_demo),
            )
            self._replace_children("organism_life_stages", "organism_id", o.id, ["life_stage_id"], [(self._stages[s.value],) for s in o.life_stages])
            self._replace_children("common_names", "organism_id", o.id, ["language", "name", "is_primary"], [(n.language, n.name, n.is_primary) for n in o.common_names])
            self._replace_children("organism_texts", "organism_id", o.id, ["language", "description", "fishing_notes"], [(t.language, t.description, t.fishing_notes) for t in o.texts])
            self._replace_children("taxonomic_synonyms", "organism_id", o.id, ["synonym", "source"], [(s, o.data_source) for s in o.synonyms])
        return len(organisms)

    def upsert_flies(self, flies: Sequence[FlyRecord]) -> int:
        for f in flies:
            self._conn.execute(
                """
                insert into fly_patterns (id, slug, name, alternate_names, category, imitation_type, hook_size_min,
                  hook_size_max, colors, habitats, fishing_environments, difficulty, data_source, verification_status, is_demo)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                on conflict (id) do update set slug = excluded.slug, name = excluded.name,
                  alternate_names = excluded.alternate_names, category = excluded.category,
                  imitation_type = excluded.imitation_type, hook_size_min = excluded.hook_size_min,
                  hook_size_max = excluded.hook_size_max, colors = excluded.colors, habitats = excluded.habitats,
                  fishing_environments = excluded.fishing_environments, difficulty = excluded.difficulty,
                  data_source = excluded.data_source, verification_status = excluded.verification_status,
                  is_demo = excluded.is_demo
                """,
                (f.id, f.slug, f.name, list(f.alternate_names), f.category.value, f.imitation_type.value, f.hook_size_min,
                 f.hook_size_max, list(f.colors), [h.value for h in f.habitats], [e.value for e in f.fishing_environments],
                 f.difficulty, f.data_source, f.verification_status.value, f.is_demo),
            )
            self._replace_children("fly_pattern_texts", "fly_pattern_id", f.id, ["language", "description", "usage_notes"], [(t.language, t.description, t.fishing_notes) for t in f.texts])
            self._replace_children("fly_pattern_materials", "fly_pattern_id", f.id, ["component", "material", "sort_order"], [(m.component, m.material, i) for i, m in enumerate(f.materials)])
            self._replace_children("fly_pattern_variants", "fly_pattern_id", f.id, ["name", "description"], [(v.name, v.description) for v in f.variants])
        return len(flies)

    def upsert_matches(self, matches: Sequence[MatchRecord]) -> int:
        with self._conn.cursor() as cur:
            cur.executemany(
                """
                insert into fly_organism_matches (id, organism_id, fly_pattern_id, life_stage_id, match_type,
                  biological_compatibility, expert_verified, verification_source, notes)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                on conflict (organism_id, fly_pattern_id, life_stage_id) do update set match_type = excluded.match_type,
                  biological_compatibility = excluded.biological_compatibility, expert_verified = excluded.expert_verified,
                  verification_source = excluded.verification_source, notes = excluded.notes
                """,
                [(m.id, m.organism_id, m.fly_pattern_id, self._stages[m.life_stage.value], m.match_type.value,
                  m.biological_compatibility.value, m.expert_verified, m.verification_source, m.notes) for m in matches],
            )
        return len(matches)

    def upsert_images(self, images: Sequence[ImageRecord]) -> int:
        for image in images:
            table, owner_col = _IMAGE_TABLES[image.owner_kind]
            columns = [
                "id", owner_col, "image_url", "storage_path", "source", "source_id", "source_url", "license",
                "attribution", "commercial_use_allowed", "permission_status", "image_view",
            ]
            values = [
                image.id, image.owner_id, image.image_url, image.storage_path, image.source, image.source_id,
                image.source_url, image.license, image.attribution, image.commercial_use_allowed,
                image.permission_status.value, image.image_view,
            ]
            if image.owner_kind == "organism":  # fly images have no life stage
                columns.append("life_stage_id")
                values.append(self._stages[image.life_stage.value] if image.life_stage else None)
            updates = ", ".join(f"{c} = excluded.{c}" for c in columns if c not in ("id", owner_col, "source", "source_id"))
            self._conn.execute(
                f"insert into {table} ({', '.join(columns)}) values ({', '.join(['%s'] * len(columns))}) "
                f"on conflict (id) do update set {updates}",
                values,
            )
        return len(images)

    def upsert_stores(self, stores: Sequence[StoreRecord]) -> int:
        with self._conn.cursor() as cur:
            cur.executemany(
                """
                insert into stores (id, slug, name, website, country, currency, description, affiliate_program,
                  shipping_countries, active, is_demo)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                on conflict (id) do update set name = excluded.name, website = excluded.website, country = excluded.country,
                  currency = excluded.currency, description = excluded.description,
                  affiliate_program = excluded.affiliate_program, shipping_countries = excluded.shipping_countries,
                  active = excluded.active, is_demo = excluded.is_demo
                """,
                [(s.id, s.slug, s.name, str(s.website), s.country, s.currency, s.description, s.affiliate_program,
                  list(s.shipping_countries), s.active, s.is_demo) for s in stores],
            )
        return len(stores)

    def upsert_products(self, products: Sequence[ProductRecord], links: Sequence[ProductPatternRecord]) -> int:
        with self._conn.cursor() as cur:
            cur.executemany(
                """
                insert into products (id, store_id, external_id, name, brand, description, product_url, affiliate_url,
                  price, currency, availability_status, country, last_verified_at, active, is_demo)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                on conflict (id) do update set name = excluded.name, brand = excluded.brand,
                  description = excluded.description, product_url = excluded.product_url,
                  affiliate_url = excluded.affiliate_url, price = excluded.price, currency = excluded.currency,
                  availability_status = excluded.availability_status, country = excluded.country,
                  last_verified_at = excluded.last_verified_at, active = excluded.active, is_demo = excluded.is_demo
                """,
                [(p.id, p.store_id, p.external_id, p.name, p.brand, p.description, str(p.product_url),
                  str(p.affiliate_url) if p.affiliate_url else None, p.price, p.currency, p.availability_status.value,
                  p.country, p.last_verified_at, p.active, p.is_demo) for p in products],
            )
            cur.executemany(
                """
                insert into product_patterns (id, product_id, fly_pattern_id, size, color, variant)
                values (%s,%s,%s,%s,%s,%s)
                on conflict (id) do update set size = excluded.size, color = excluded.color, variant = excluded.variant
                """,
                [(link.id, link.product_id, link.fly_pattern_id, link.size, link.color, link.variant) for link in links],
            )
        return len(products)

    def write(self, dataset: CatalogDataset) -> dict[str, int]:
        return {
            "organisms": self.upsert_organisms(dataset.organisms),
            "flies": self.upsert_flies(dataset.flies),
            "matches": self.upsert_matches(dataset.matches),
            "images": self.upsert_images(dataset.images),
            "stores": self.upsert_stores(dataset.stores),
            "products": self.upsert_products(dataset.products, dataset.product_patterns),
        }


class PgVectorIndex:
    def __init__(self, pool: ConnectionPool):
        self._pool = pool

    def search(self, owner_kind: str, embedding: np.ndarray, model: str, k: int = 10) -> list[VectorHit]:
        table, owner_col = _IMAGE_TABLES[owner_kind]
        vector = np.asarray(embedding, dtype=np.float32)
        with self._pool.connection() as conn:
            rows = conn.execute(
                f"""
                select id, {owner_col} as owner_id, 1 - (embedding <=> %s) as similarity
                from {table}
                where embedding is not null and embedding_model = %s and permission_status = 'approved'
                order by embedding <=> %s
                limit %s
                """,
                (vector, model, vector, k * 4),
            ).fetchall()
        hits = [VectorHit(image_id=r["id"], owner_kind=owner_kind, owner_id=r["owner_id"], similarity=float(r["similarity"])) for r in rows]
        return aggregate_by_owner(hits, k)


class PgEmbeddingStore:
    def __init__(self, conn: Connection):
        self._conn = conn

    def images_missing_embedding(self, owner_kind: str, model: str, limit: int) -> list[dict]:
        table, owner_col = _IMAGE_TABLES[owner_kind]
        return self._conn.execute(
            f"""
            select id, {owner_col} as owner_id, image_url, storage_path from {table}
            where permission_status = 'approved' and (embedding is null or embedding_model is distinct from %s)
            order by created_at limit %s
            """,
            (model, limit),
        ).fetchall()

    def save_embedding(self, owner_kind: str, image_id: uuid.UUID, model: str, embedding: np.ndarray) -> None:
        table, _ = _IMAGE_TABLES[owner_kind]
        self._conn.execute(
            f"update {table} set embedding = %s, embedding_model = %s where id = %s",
            (np.asarray(embedding, dtype=np.float32), model, image_id),
        )


class PgIdentificationStore:
    def __init__(self, pool: ConnectionPool):
        self._pool = pool

    def save(self, record: IdentificationRecord) -> None:
        with self._pool.connection() as conn, conn.transaction():
            conn.execute(
                """
                insert into identifications (id, client_hash, kind, match_level, primary_label, result, analysis_source,
                  ai_model, embedding_model, image_consent, image_storage_path, is_demo, created_at)
                values (%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s)
                """,
                (record.id, record.client_hash, record.kind, record.match_level, record.primary_label,
                 json.dumps(record.result, default=str), record.analysis_source, record.ai_model, record.embedding_model,
                 record.image_consent, record.image_storage_path, record.is_demo, record.created_at),
            )
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    insert into identification_candidates (identification_id, position, label, organism_id, fly_pattern_id,
                      ai_confidence, visual_similarity)
                    values (%s,%s,%s,%s,%s,%s,%s)
                    """,
                    [(record.id, c.position, c.label, c.organism_id, c.fly_pattern_id, c.ai_confidence, c.visual_similarity)
                     for c in record.candidates],
                )

    _COLUMNS = (
        "id, client_hash, kind, match_level, primary_label, result, analysis_source, ai_model, "
        "embedding_model, image_consent, image_storage_path, is_demo, created_at"
    )

    def list_for_client(self, client_hash: str, limit: int) -> list[IdentificationRecord]:
        with self._pool.connection() as conn:
            rows = conn.execute(
                f"select {self._COLUMNS} from identifications where client_hash = %s order by created_at desc limit %s",
                (client_hash, limit),
            ).fetchall()
        return [IdentificationRecord(**r) for r in rows]

    def get_for_client(self, identification_id: uuid.UUID, client_hash: str) -> IdentificationRecord | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                f"select {self._COLUMNS} from identifications where id = %s and client_hash = %s",
                (identification_id, client_hash),
            ).fetchone()
        return IdentificationRecord(**row) if row else None
