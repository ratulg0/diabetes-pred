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
_retraining_lock = Lock()


@router.get("", response_model=ModelStatusResponse)
def model_status(model_registry: ModelRegistry = Depends(get_model_registry)) -> ModelStatusResponse:
    current = model_registry.status()
    if current["available"]:
        return ModelStatusResponse(available=True, metadata=current["metadata"])
    return ModelStatusResponse(available=False, reason=current["reason"])


@router.post("/retrain-all", response_model=ModelStatusResponse)
async def retrain_all_models(
    request: Request,
    model_registry: ModelRegistry = Depends(get_model_registry),
) -> ModelStatusResponse:
    """Retrain all four candidates and activate their soft-voting ensemble."""
    if not _retraining_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Model training is already running. Please wait for it to finish.",
        )
    try:
        settings: Settings = request.app.state.settings
        metadata = await asyncio.to_thread(
            train_and_select,
            settings.dataset_path,
            settings.resolved_model_artifact_path,
            None,
        )
        model_registry.reload()
        logger.info("ensemble_retrained version=%s members=%s", metadata["version"], metadata["members"])
        return ModelStatusResponse(available=True, metadata=metadata)
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
