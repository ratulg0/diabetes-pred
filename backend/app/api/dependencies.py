# FastAPI dependency providers for database sessions and the model registry.
# Each dependency resolves runtime state stored on the FastAPI app object.
from __future__ import annotations

from collections.abc import Generator

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import Database
from app.ml.registry import ModelRegistry


def get_database(request: Request) -> Database:
    # Return the configured database or 503 if it is unavailable.
    database: Database | None = getattr(request.app.state, "database", None)
    if database is None or not database.is_available():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database is not configured or unavailable.")
    return database


def get_session(request: Request) -> Generator[Session, None, None]:
    # Yield a database session for the request lifecycle.
    database = get_database(request)
    yield from database.session()


def get_model_registry(request: Request) -> ModelRegistry:
    # Return the cached model registry instance from app state.
    return request.app.state.model_registry
