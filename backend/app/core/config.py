from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
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
        return [origin.strip() for origin in value.split(",") if origin.strip()] if isinstance(value, str) else value

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    @property
    def dataset_path(self) -> Path:
        # The clinical assessment and training pipeline use the supplied 20k-row dataset.
        return self.project_root / "data" / "raw" / "Diabetes Dataset.csv"

    @property
    def resolved_model_artifact_path(self) -> Path:
        return self.model_artifact_path or self.project_root / "models" / "active-model.joblib"

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        local_path = self.project_root / "backend" / ".local" / "glucocare.db"
        return f"sqlite:///{local_path.as_posix()}"

    @property
    def uses_local_development_database(self) -> bool:
        return self.database_url is None


@lru_cache
def get_settings() -> Settings:
    return Settings()
