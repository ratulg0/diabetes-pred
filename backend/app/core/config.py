# Runtime configuration loaded from environment variables or a local .env file.
# All settings have sensible development defaults and are validated by pydantic.
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])
    database_url: str | None = None
    model_artifact_path: Path | None = None
    model_version: str | None = None
    log_level: str = "INFO"
    allow_destructive_demo_actions: bool = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: str | list[str]) -> list[str]:
        # Allow CORS origins to be supplied as either a comma-separated string or a list.
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def project_root(self) -> Path:
        # Repository root, three levels up from this file (backend/app/core -> repo root).
        return Path(__file__).resolve().parents[3]

    @property
    def dataset_path(self) -> Path:
        # Root-level diabetes.csv used for training and audit.
        return self.project_root / "diabetes.csv"

    @property
    def resolved_model_artifact_path(self) -> Path:
        # Default artifact location under backend/models/ unless overridden.
        return self.model_artifact_path or self.project_root / "models" / "active-model.joblib"

    @property
    def resolved_database_url(self) -> str:
        # Fall back to a local SQLite dev database when no DATABASE_URL is configured.
        if self.database_url:
            return self.database_url
        local_path = self.project_root / "backend" / ".local" / "glucocare.db"
        return f"sqlite:///{local_path.as_posix()}"

    @property
    def uses_local_development_database(self) -> bool:
        # True when operating without an external deployment database.
        return self.database_url is None


@lru_cache
def get_settings() -> Settings:
    # Cache settings so environment parsing happens once per process.
    return Settings()
