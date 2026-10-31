"""Centralized, validated configuration loaded from environment / backend/.env."""

from __future__ import annotations

import re
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent
_DEV_SALT = "dev-only-insecure-salt"


class Environment(str, Enum):
    development = "development"
    staging = "staging"
    production = "production"


class CatalogBackend(str, Enum):
    memory = "memory"
    postgres = "postgres"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Environment = Environment.development
    app_name: str = "Fly Finder"
    log_level: str = "INFO"
    cors_origins: list[str] = Field(default_factory=list)

    catalog_backend: CatalogBackend = CatalogBackend.memory
    catalog_dir: Path = REPO_ROOT / "data" / "catalog"
    demo_mode: bool = False
    demo_dir: Path = REPO_ROOT / "data" / "demo"

    supabase_url: str | None = None
    supabase_service_role_key: SecretStr | None = None
    database_url: SecretStr | None = None
    supabase_storage_bucket_catalog: str = "catalog-images"
    supabase_storage_bucket_user: str = "user-uploads"

    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-3.8-flash"
    gemini_timeout_seconds: float = 45.0
    # generation_config.thinking_level (https://ai.google.dev/gemini-api/docs/thinking). The model
    # default (medium) took 20-45 s per photo; lower thinking is the documented way to cut latency.
    gemini_thinking_level: Literal["low", "medium", "high"] = "low"

    embeddings_enabled: bool = True
    openclip_model: str = "ViT-B-32"
    openclip_pretrained: str = "laion2b_s34b_b79k"
    openclip_device: str = "cpu"
    # Must match the vector(...) dimension in the SQL migrations.
    embedding_dimension: int = 512

    gbif_api_url: str = "https://api.gbif.org/v1"
    inaturalist_api_url: str = "https://api.inaturalist.org/v1"
    external_user_agent: str = "FlyFinder/0.1 (https://github.com/Chab8/Fly-Finder)"
    external_timeout_seconds: float = 8.0

    # Salt for hashing anonymous client ids before storing them. Set a long random value
    # in staging/production (e.g. `python -c "import secrets; print(secrets.token_urlsafe(32))"`).
    client_hash_salt: SecretStr = SecretStr(_DEV_SALT)
    catalog_refresh_seconds: int = Field(default=300, ge=10)

    max_upload_mb: int = Field(default=12, ge=1, le=20)
    identify_rate_limit_per_minute: int = Field(default=10, ge=1)
    allow_user_image_storage: bool = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [v.strip() for v in value.split(",") if v.strip()]
        return value

    @field_validator(
        "supabase_url", "supabase_service_role_key", "database_url", "gemini_api_key",
        mode="before",
    )
    @classmethod
    def _empty_to_none(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("supabase_url")
    @classmethod
    def _project_url(cls, value: str | None) -> str | None:
        # The dashboard also shows the REST endpoint (.../rest/v1/); Storage needs the project root.
        if value is None:
            return None
        return re.sub(r"/rest/v1/?$", "", value.rstrip("/"))

    @field_validator("client_hash_salt", mode="before")
    @classmethod
    def _default_salt(cls, value: object) -> object:
        return _DEV_SALT if value in ("", None) else value

    @model_validator(mode="after")
    def _check_consistency(self) -> Settings:
        if self.catalog_backend == CatalogBackend.postgres and not self.database_url:
            raise ValueError("CATALOG_BACKEND=postgres requires DATABASE_URL")
        if self.environment == Environment.production:
            if self.demo_mode:
                raise ValueError("DEMO_MODE must be false in production")
            if self.catalog_backend != CatalogBackend.postgres:
                raise ValueError("production requires CATALOG_BACKEND=postgres")
            if self.client_hash_salt.get_secret_value() == _DEV_SALT:
                raise ValueError("CLIENT_HASH_SALT must be set in production")
            if "*" in self.cors_origins:
                raise ValueError("wildcard CORS origin is not allowed in production")
        return self

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def gemini_configured(self) -> bool:
        return self.gemini_api_key is not None

    @property
    def embedding_model_id(self) -> str:
        """Identifier stored next to every embedding so vectors from different models never mix."""
        return f"open_clip:{self.openclip_model}:{self.openclip_pretrained}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
