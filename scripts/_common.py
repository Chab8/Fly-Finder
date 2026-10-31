"""Shared helpers for the catalog scripts. Run scripts from the repository root with the
backend virtualenv, e.g.:  backend/.venv/bin/python scripts/validate_dataset.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.catalog.csv_loader import LoadResult, load_catalog_dir  # noqa: E402
from app.catalog.validation import validate_dataset  # noqa: E402
from app.core.config import Settings, get_settings  # noqa: E402

DEFAULT_CATALOG_DIR = REPO_ROOT / "data" / "catalog"


def base_parser(description: str, *, writes_db: bool = False) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--dir", type=Path, default=DEFAULT_CATALOG_DIR, help="Folder with the catalog CSV files")
    if writes_db:
        parser.add_argument(
            "--apply", action="store_true",
            help="Write to the database in DATABASE_URL. Without it the script only validates (dry run).",
        )
    return parser


def load_and_validate(directory: Path, *, quiet_warnings: bool = False) -> LoadResult:
    result = load_catalog_dir(directory)
    result.issues += validate_dataset(result.dataset)
    for issue in result.issues:
        if issue.severity == "error" or not quiet_warnings:
            print(issue)
    d = result.dataset
    print(
        f"Loaded {len(d.organisms)} organisms, {len(d.flies)} fly patterns, {len(d.matches)} relations, "
        f"{len(d.images)} images, {len(d.stores)} stores, {len(d.products)} products "
        f"({len(result.errors)} errors, {len(result.issues) - len(result.errors)} warnings)"
    )
    return result


def require_database(settings: Settings | None = None):
    """Open a psycopg connection to DATABASE_URL (Supabase session pooler)."""
    import psycopg
    from pgvector.psycopg import register_vector
    from psycopg.rows import dict_row

    settings = settings or get_settings()
    if not settings.database_url:
        sys.exit("DATABASE_URL is not set in backend/.env (see docs/DATABASE_SETUP.md).")
    conn = psycopg.connect(settings.database_url.get_secret_value(), row_factory=dict_row, connect_timeout=15)
    conn.execute("set search_path = public, extensions")
    register_vector(conn)
    return conn


def write_dataset(result: LoadResult, apply: bool, sections: list[str]) -> None:
    """Upsert the requested sections in a single transaction (all-or-nothing)."""
    if result.errors:
        sys.exit("Fix the errors above before importing.")
    if not apply:
        print("Dry run: nothing was written. Re-run with --apply to import.")
        return
    from app.repositories.postgres import PgCatalogWriter

    with require_database() as conn, conn.transaction():
        writer = PgCatalogWriter(conn)
        d = result.dataset
        counts = {}
        if "organisms" in sections:
            counts["organisms"] = writer.upsert_organisms(d.organisms)
        if "flies" in sections:
            counts["flies"] = writer.upsert_flies(d.flies)
        if "matches" in sections:
            counts["matches"] = writer.upsert_matches(d.matches)
        if "images" in sections:
            counts["images"] = writer.upsert_images(d.images)
        if "stores" in sections:
            counts["stores"] = writer.upsert_stores(d.stores)
        if "products" in sections:
            counts["products"] = writer.upsert_products(d.products, d.product_patterns)
    print("Imported:", ", ".join(f"{k}={v}" for k, v in counts.items()))
