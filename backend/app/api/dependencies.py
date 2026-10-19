from __future__ import annotations

from collections.abc import Generator

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import Database
from app.ml.registry import ModelRegistry


def get_database(request: Request) -> Database:
    database: Database | None = getattr(request.app.state, "database", None)
    if database is None or not database.is_available():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database is not configured or unavailable.")
    return database


def get_session(request: Request) -> Generator[Session, None, None]:
    database = get_database(request)
    yield from database.session()


def get_model_registry(request: Request) -> ModelRegistry:
    return request.app.state.model_registry
