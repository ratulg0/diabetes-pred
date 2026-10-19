from __future__ import annotations

import logging
from threading import Lock

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies import get_model_registry
from app.core.config import Settings
from app.ml.registry import ModelRegistry
from app.ml.train import retrain_candidate
from app.schemas.models import ModelStatusResponse

router = APIRouter(prefix="/models", tags=["models"])
logger = logging.getLogger("glucocare.models")
_retraining_lock = Lock()
SUPPORTED_MODELS = {
    "logistic_regression",
    "random_forest",
    "xgboost",
    "hist_gradient_boosting",
}


@router.get("", response_model=ModelStatusResponse)
def model_status(model_registry: ModelRegistry = Depends(get_model_registry)) -> ModelStatusResponse:
    current = model_registry.status()
    if current["available"]:
        return ModelStatusResponse(available=True, metadata=current["metadata"])
    return ModelStatusResponse(available=False, reason=current["reason"])


@router.post("/retrain/{model_name}", response_model=ModelStatusResponse)
def retrain_model(
    model_name: str,
    request: Request,
    model_registry: ModelRegistry = Depends(get_model_registry),
) -> ModelStatusResponse:
    """Retrain one candidate and activate it for subsequent assessments."""
    if model_name not in SUPPORTED_MODELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported model. Choose one of: {', '.join(sorted(SUPPORTED_MODELS))}.",
        )

    if not _retraining_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A model retraining job is already running. Please wait for it to finish.",
        )
    try:
        settings: Settings = request.app.state.settings
        existing = model_registry.status()
        previous_metadata = existing.get("metadata") if existing.get("available") else None
        metadata = retrain_candidate(
            settings.dataset_path,
            settings.resolved_model_artifact_path,
            model_name,
            settings.model_version,
            previous_metadata,
        )
        model_registry.reload()
        logger.info("model_retrained model=%s version=%s", model_name, metadata["version"])
        return ModelStatusResponse(available=True, metadata=metadata)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except Exception as error:
        logger.exception("model_retraining_failed model=%s", model_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The model could not be retrained. Check the backend logs for details.",
        ) from error
    finally:
        _retraining_lock.release()
