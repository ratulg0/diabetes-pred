from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_model_registry
from app.ml.registry import ModelRegistry
from app.schemas.models import ModelStatusResponse

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=ModelStatusResponse)
def model_status(model_registry: ModelRegistry = Depends(get_model_registry)) -> ModelStatusResponse:
    status = model_registry.status()
    if status["available"]:
        return ModelStatusResponse(available=True, metadata=status["metadata"])
    return ModelStatusResponse(available=False, reason=status["reason"])
