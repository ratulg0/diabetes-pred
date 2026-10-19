# Business logic for running lifestyle model predictions and persisting records.
from __future__ import annotations

import json
from pathlib import Path

import joblib
from sqlalchemy.orm import Session

from app.db.models import LifestyleAssessment
from app.ml.schema import DISCLAIMER
from app.repositories.lifestyle_assessments import LifestyleAssessmentRepository
from app.schemas.lifestyle_assessments import (
    LifestyleAssessmentInput,
    LifestyleAssessmentRecord,
    LifestylePredictionResponse,
    ModelIdentity,
)


class LifestyleAssessmentService:
    def __init__(self, repository: LifestyleAssessmentRepository | None = None) -> None:
        self.repository = repository or LifestyleAssessmentRepository()

    def _load_artifact(self) -> tuple[object, dict]:
        # Load the trained lifestyle artifact package from disk.
        path = Path(__file__).resolve().parents[3] / "models" / "lifestyle" / "active-model.joblib"
        if not path.is_file():
            raise FileNotFoundError("Lifestyle model artifact is not available.")
        package = joblib.load(path)
        if not isinstance(package, dict) or "pipeline" not in package or "metadata" not in package:
            raise ValueError("The lifestyle model artifact has an invalid package format.")
        return package["pipeline"], package["metadata"]

    def predict(self, inputs: LifestyleAssessmentInput) -> LifestylePredictionResponse:
        # Run inference against the trusted lifestyle artifact without persisting.
        pipeline, metadata = self._load_artifact()
        probability = float(pipeline.predict_proba(inputs.feature_frame())[0, 1])
        predicted_class = int(probability >= float(metadata.get("threshold", 0.5)))
        return LifestylePredictionResponse(
            prediction_id="not-persisted",
            predicted_class=predicted_class,
            prediction_label=(
                "Survey profile is in the dataset's prediabetes/diabetes positive class"
                if predicted_class
                else "Survey profile is in the dataset's no-diabetes class"
            ),
            probability=probability,
            model_accuracy=self._test_accuracy(metadata),
            model=ModelIdentity(name=str(metadata["name"]), version=str(metadata["version"])),
            target_definition=metadata.get(
                "target_semantics",
                "1 combines prediabetes and diabetes; 0 indicates no diabetes in source survey.",
            ),
            disclaimer=DISCLAIMER,
        )

    def predict_and_save(self, session: Session, inputs: LifestyleAssessmentInput) -> LifestyleAssessmentRecord:
        # Run inference and persist lifestyle assessment plus prediction result atomically.
        pipeline, metadata = self._load_artifact()
        probability = float(pipeline.predict_proba(inputs.feature_frame())[0, 1])
        predicted_class = int(probability >= float(metadata.get("threshold", 0.5)))
        assessment = self.repository.create_with_result(
            session=session,
            inputs=inputs,
            predicted_class=predicted_class,
            probability=probability,
            model_accuracy=self._test_accuracy(metadata),
            model_name=str(metadata["name"]),
            model_version=str(metadata["version"]),
        )
        return self._assessment_to_record(assessment)

    def _test_accuracy(self, metadata: dict) -> float | None:
        # Extract held-out test accuracy from artifact metadata if present.
        metrics = metadata.get("test_metrics", {})
        accuracy = metrics.get("accuracy") if isinstance(metrics, dict) else None
        return float(accuracy) if isinstance(accuracy, (int, float)) else None

    def _assessment_to_record(self, assessment: LifestyleAssessment) -> LifestyleAssessmentRecord:
        # Hydrate a persisted LifestyleAssessment ORM row into an API response schema.
        if assessment.result is None:
            raise ValueError("Persisted lifestyle assessment is missing its prediction result.")
        try:
            response_metadata = json.loads(assessment.result.response_metadata or "{}")
        except (TypeError, json.JSONDecodeError):
            response_metadata = {}
        return LifestyleAssessmentRecord(
            prediction_id=assessment.id,
            predicted_class=assessment.result.predicted_class,
            prediction_label=(
                "Survey profile is in the dataset's prediabetes/diabetes positive class"
                if assessment.result.predicted_class
                else "Survey profile is in the dataset's no-diabetes class"
            ),
            probability=assessment.result.probability,
            model_accuracy=response_metadata.get("model_accuracy"),
            model=ModelIdentity(name=assessment.result.model_name, version=assessment.result.model_version),
            target_definition="1 combines prediabetes and diabetes; 0 indicates no diabetes in source survey.",
            disclaimer=DISCLAIMER,
            created_at=assessment.created_at,
            source=assessment.source,
            input=LifestyleAssessmentInput(
                high_bp=assessment.high_bp,
                high_chol=assessment.high_chol,
                chol_check=assessment.chol_check,
                bmi=assessment.bmi,
                smoker=assessment.smoker,
                stroke=assessment.stroke,
                heart_disease_or_attack=assessment.heart_disease_or_attack,
                phys_activity=assessment.phys_activity,
                fruits=assessment.fruits,
                veggies=assessment.veggies,
                hvy_alcohol_consump=assessment.hvy_alcohol_consump,
                any_healthcare=assessment.any_healthcare,
                no_docbc_cost=assessment.no_docbc_cost,
                gen_hlth=assessment.gen_hlth,
                ment_hlth=assessment.ment_hlth,
                phys_hlth=assessment.phys_hlth,
                diff_walk=assessment.diff_walk,
                sex=assessment.sex,
                age=assessment.age,
                education=assessment.education,
                income=assessment.income,
            ),
        )
