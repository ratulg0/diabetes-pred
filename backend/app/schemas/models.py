from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ModelStatusResponse(BaseModel):
    available: bool
    metadata: dict[str, Any] | None = None
    reason: str | None = None
