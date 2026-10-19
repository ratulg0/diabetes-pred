# Pydantic models shared across multiple API responses. These define the
# standardized shape of error, health, and readiness payloads.
from __future__ import annotations

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error envelope returned for client and server failures."""
    code: str
    message: str
    request_id: str


class HealthResponse(BaseModel):
    """Process liveness probe response."""
    status: str


class ReadinessResponse(BaseModel):
    """Readiness probe response reporting database and model availability."""
    status: str
    database: str
    model: str
    detail: str | None = None
