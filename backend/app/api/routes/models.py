# Model status and retraining routes for the active replacement-dataset classifier.
from __future__ import annotations

import asyncio
import logging
from threading import Lock

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies import get_model_registry
from app.core.config import Settings
from app.ml.registry import ModelRegistry
from app.ml.train import train_and_select
from app.schemas.models import ModelStatusResponse

router = APIRouter(prefix="/models", tags=["models"])
logger = logging.getLogger("glucocare.models")
# Serialize retraining so only one training job runs at a time.
_retraining_lock = Lock()


@router.get("", response_model=ModelStatusResponse)
def model_status(
    request: Request,
    model_registry: ModelRegistry = Depends(get_model_registry),
) -> ModelStatusResponse:
    # Return whether a trusted artifact is available along with its metadata.
    current = model_registry.status()
    if current["available"]:
        return ModelStatusResponse(available=True, metadata=current["metadata"])
    settings: Settings = request.app.state.settings
    if not settings.dataset_path.is_file():
        return ModelStatusResponse(
            available=False,
            reason=f"Replacement clinical dataset is missing: {settings.dataset_path}",
        )
    return ModelStatusResponse(available=False, reason=current["reason"])


@router.post("/retrain-all", response_model=ModelStatusResponse)
async def retrain_all_models(
    request: Request,
    model_registry: ModelRegistry = Depends(get_model_registry),
) -> ModelStatusResponse:
    """Re-evaluate the supported candidates and activate the best replacement-dataset model."""
    # Guard against concurrent retraining jobs.
    if not _retraining_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Model training is already running. Please wait for it to finish.",
        )
    try:
        settings: Settings = request.app.state.settings
        if not settings.dataset_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Replacement clinical dataset is missing: {settings.dataset_path}",
            )
        metadata = await asyncio.to_thread(
            train_and_select,
            settings.dataset_path,
            settings.resolved_model_artifact_path,
            None,
        )
        model_registry.reload()
        logger.info("clinical_model_retrained version=%s selected=%s", metadata["version"], metadata["name"])
        return ModelStatusResponse(available=True, metadata=metadata)
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except Exception as error:
        logger.exception("ensemble_retraining_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The models could not be retrained. Check the backend logs for details.",
        ) from error
    finally:
        _retraining_lock.release()
