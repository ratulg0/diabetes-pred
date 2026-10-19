# Schema describing the model-status and retrain-all response payloads.
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ModelStatusResponse(BaseModel):
    """Whether a trusted model artifact is available, plus its metadata."""
    available: bool
    metadata: dict[str, Any] | None = None
    reason: str | None = None
