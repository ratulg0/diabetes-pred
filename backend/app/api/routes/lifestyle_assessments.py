"""CDC lifestyle model prediction and persistence endpoints."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_session
from app.ml.schema import DISCLAIMER
from app.repositories.lifestyle_assessments import LifestyleAssessmentRepository
from app.schemas.lifestyle_assessments import (
    LifestyleAssessmentInput,
    LifestyleAssessmentPage,
    LifestyleAssessmentRecord,
    LifestylePredictionResponse,
    ModelIdentity,
)
from app.services.lifestyle_assessments import LifestyleAssessmentService

router = APIRouter(prefix="/lifestyle-assessments", tags=["lifestyle-assessments"])

FEATURES = [
    "HighBP",
    "HighChol",
    "CholCheck",
    "BMI",
    "Smoker",
    "Stroke",
    "HeartDiseaseorAttack",
    "PhysActivity",
    "Fruits",
    "Veggies",
    "HvyAlcoholConsump",
    "AnyHealthcare",
    "NoDocbcCost",
    "GenHlth",
    "MentHlth",
    "PhysHlth",
    "DiffWalk",
    "Sex",
    "Age",
    "Education",
    "Income",
]
KEYS = [
    "high_bp",
    "high_chol",
    "chol_check",
    "bmi",
    "smoker",
    "stroke",
    "heart_disease_or_attack",
    "phys_activity",
    "fruits",
    "veggies",
    "hvy_alcohol_consump",
    "any_healthcare",
    "no_docbc_cost",
    "gen_hlth",
    "ment_hlth",
    "phys_hlth",
    "diff_walk",
    "sex",
    "age",
    "education",
    "income",
]


def artifact_path() -> Path:
    return Path(__file__).resolve().parents[4] / "models" / "lifestyle" / "active-model.joblib"


def service(session: Session = Depends(get_session)) -> LifestyleAssessmentService:
    return LifestyleAssessmentService()


@router.get("/status")
def status_lifestyle() -> dict[str, Any]:
    path = artifact_path()
    if not path.is_file():
        return {
            "available": False,
            "reason": "Run python -m app.ml.train_lifestyle from the backend directory.",
        }
    try:
        package = joblib.load(path)
        metadata = package.get("metadata", {})
        if metadata.get("feature_schema") != FEATURES:
            return {"available": False, "reason": "Lifestyle artifact schema mismatch."}
        return {"available": True, "metadata": metadata}
    except Exception:
        return {"available": False, "reason": "Lifestyle artifact could not be loaded."}


@router.post("/predict", response_model=LifestylePredictionResponse)
def predict_lifestyle(
    inputs: LifestyleAssessmentInput,
    lifestyle_service: LifestyleAssessmentService = Depends(service),
) -> LifestylePredictionResponse:
    # Run inference only; no database write. Returns 503 if model unavailable.
    try:
        return lifestyle_service.predict(inputs)
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Lifestyle model is not trained. Run python -m app.ml.train_lifestyle.",
        ) from error
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Lifestyle artifact is invalid or incompatible.",
        ) from exc


@router.post("/save", response_model=LifestyleAssessmentRecord, status_code=status.HTTP_201_CREATED)
def save_lifestyle(
    inputs: LifestyleAssessmentInput,
    lifestyle_service: LifestyleAssessmentService = Depends(service),
    session: Session = Depends(get_session),
) -> LifestyleAssessmentRecord:
    # Run inference and persist lifestyle assessment plus prediction result.
    try:
        return lifestyle_service.predict_and_save(session, inputs)
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Lifestyle model is not trained. Run python -m app.ml.train_lifestyle.",
        ) from error
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Lifestyle assessment could not be saved.",
        ) from exc


@router.get("/history", response_model=LifestyleAssessmentPage)
def list_lifestyle_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    predicted_class: int | None = Query(default=None, ge=0, le=1),
    session: Session = Depends(get_session),
) -> LifestyleAssessmentPage:
    # Return a paginated page of saved lifestyle assessment records.
    repository = LifestyleAssessmentRepository()
    items, total = repository.list(
        session,
        offset=(page - 1) * page_size,
        limit=page_size,
        predicted_class=predicted_class,
    )
    records = [
        LifestyleAssessmentRecord(
            prediction_id=item.id,
            predicted_class=item.result.predicted_class if item.result else 0,
            prediction_label=(
                "Survey profile is in the dataset's prediabetes/diabetes positive class"
                if item.result and item.result.predicted_class
                else "Survey profile is in the dataset's no-diabetes class"
            ),
            probability=item.result.probability if item.result else None,
            model_accuracy=None,
            model=ModelIdentity(
                name=item.result.model_name if item.result else "unknown",
                version=item.result.model_version if item.result else "unknown",
            ),
            target_definition="1 combines prediabetes and diabetes; 0 indicates no diabetes in source survey.",
            disclaimer=DISCLAIMER,
            created_at=item.created_at,
            source=item.source,
            input=LifestyleAssessmentInput(
                high_bp=item.high_bp,
                high_chol=item.high_chol,
                chol_check=item.chol_check,
                bmi=item.bmi,
                smoker=item.smoker,
                stroke=item.stroke,
                heart_disease_or_attack=item.heart_disease_or_attack,
                phys_activity=item.phys_activity,
                fruits=item.fruits,
                veggies=item.veggies,
                hvy_alcohol_consump=item.hvy_alcohol_consump,
                any_healthcare=item.any_healthcare,
                no_docbc_cost=item.no_docbc_cost,
                gen_hlth=item.gen_hlth,
                ment_hlth=item.ment_hlth,
                phys_hlth=item.phys_hlth,
                diff_walk=item.diff_walk,
                sex=item.sex,
                age=item.age,
                education=item.education,
                income=item.income,
            ),
        )
        for item in items
    ]
    return LifestyleAssessmentPage(
        items=records,
        page=page,
        page_size=page_size,
        total_count=total,
    )
