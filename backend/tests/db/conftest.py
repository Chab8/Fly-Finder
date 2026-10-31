"""Throwaway PostgreSQL cluster with pgvector, migrated with the real Supabase migrations.

Skipped automatically when initdb/pg_ctl or the pgvector extension are not installed.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path

import psycopg
import pytest

from app.core.config import REPO_ROOT

STUBS = Path(__file__).with_name("supabase_stubs.sql")
MIGRATIONS = sorted((REPO_ROOT / "supabase" / "migrations").glob("*.sql"))


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def pg_url():
    if not (shutil.which("initdb") and shutil.which("pg_ctl")):
        pytest.skip("PostgreSQL binaries not installed")
    sharedir = subprocess.run(["pg_config", "--sharedir"], capture_output=True, text=True).stdout.strip()
    if not Path(sharedir, "extension", "vector.control").exists():
        pytest.skip("pgvector extension not installed (brew install pgvector)")

    env = {**os.environ, "LC_ALL": "en_US.UTF-8"}
    data_dir = Path(tempfile.mkdtemp(prefix="ffpg"))
    port = _free_port()
    subprocess.run(["initdb", "-D", str(data_dir), "-U", "postgres", "-A", "trust"], check=True, capture_output=True, env=env)
    subprocess.run(
        ["pg_ctl", "-D", str(data_dir), "-w", "-l", str(data_dir / "log.txt"),
         "-o", f"-p {port} -c unix_socket_directories='' -c listen_addresses=127.0.0.1", "start"],
        check=True, capture_output=True, env=env,
    )
    url = f"postgresql://postgres@127.0.0.1:{port}/postgres"
    try:
        with psycopg.connect(url, autocommit=True) as conn:
            conn.execute(STUBS.read_text())
            for migration in MIGRATIONS:
                conn.execute(migration.read_text())
        yield url
    finally:
        subprocess.run(["pg_ctl", "-D", str(data_dir), "-m", "fast", "stop"], capture_output=True, env=env)
        shutil.rmtree(data_dir, ignore_errors=True)
