from __future__ import annotations

from fastapi import APIRouter, Request, Response, status

from app.db.session import Database
from app.ml.registry import ModelRegistry
from app.schemas.common import HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadinessResponse)
def readiness(request: Request, response: Response) -> ReadinessResponse:
    database: Database | None = getattr(request.app.state, "database", None)
    model_registry: ModelRegistry = request.app.state.model_registry
    database_ready = database is not None and database.is_available()
    model_ready = bool(model_registry.status()["available"])
    if database_ready and model_ready:
        return ReadinessResponse(status="ready", database="ready", model="ready")
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(
        status="degraded",
        database="ready" if database_ready else "unavailable",
        model="ready" if model_ready else "unavailable",
        detail="Predictions require both a configured database and a trusted trained model artifact.",
    )
