"""Stateless predictions using the uploaded 20,000-row dataset model."""
from __future__ import annotations

import logging
from pathlib import Path

import joblib
import pandas as pd
from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import Settings
from app.ml.uploaded_dataset import DISCLAIMER, train_uploaded_dataset
from app.schemas.dataset_assessments import DatasetAssessmentInput, DatasetPredictionResponse

logger = logging.getLogger("glucocare.dataset_assessments")
router = APIRouter(prefix="/dataset-assessments", tags=["uploaded-dataset-assessments"])


def _artifact_path(settings: Settings) -> Path:
    return settings.project_root / "models" / "uploaded-dataset-model.joblib"


def _load_model(request: Request):
    settings: Settings = request.app.state.settings
    artifact = _artifact_path(settings)
    if not artifact.exists():
        dataset = settings.project_root / "data" / "raw" / "Diabetes Dataset.csv"
        if dataset.exists():
            try:
                train_uploaded_dataset(dataset, artifact)
            except Exception as exc:
                logger.exception("uploaded_dataset_training_failed")
                raise HTTPException(status_code=503, detail="Uploaded-dataset model could not be trained. Check the dataset and backend logs.") from exc
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Uploaded-dataset model is not trained. Place 'Diabetes Dataset.csv' in data/raw and run the training command in README.",
            )
    try:
        return joblib.load(artifact)
    except Exception as exc:
        logger.exception("uploaded_dataset_model_load_failed")
        raise HTTPException(status_code=503, detail="Uploaded-dataset model artifact is unavailable or invalid.") from exc


@router.post("/predict", response_model=DatasetPredictionResponse)
def predict(inputs: DatasetAssessmentInput, request: Request) -> DatasetPredictionResponse:
    package = _load_model(request)
    features = pd.DataFrame([inputs.to_features()])
    probability = float(package["pipeline"].predict_proba(features)[0, 1])
    label = "Diabetic" if probability >= 0.5 else "Non-diabetic"
    metrics = package.get("metrics", {})
    return DatasetPredictionResponse(
        prediction_label=label, probability=probability,
        model_name=package.get("model_name", "unknown"),
        metrics={key: value for key, value in metrics.items() if isinstance(value, (int, float, str))},
        disclaimer=DISCLAIMER,
    )
