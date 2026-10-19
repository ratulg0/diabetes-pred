from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.db.models import Assessment
from app.ml.registry import ModelRegistry
from app.ml.schema import DISCLAIMER, TARGET_NEGATIVE, TARGET_POSITIVE
from app.repositories.assessments import AssessmentRepository
from app.schemas.assessments import AssessmentInput, AssessmentRecord, ModelIdentity, PredictionResponse


class AssessmentService:
    def __init__(self, model_registry: ModelRegistry, repository: AssessmentRepository | None = None) -> None:
        self.model_registry = model_registry
        self.repository = repository or AssessmentRepository()

    def predict(self, inputs: AssessmentInput) -> PredictionResponse:
        predicted_class, probability, metadata = self.model_registry.predict(inputs.canonical_features())
        return PredictionResponse(
            prediction_id="not-persisted",
            predicted_class=predicted_class,
            prediction_label=prediction_label(predicted_class),
            probability=probability,
            model_accuracy=_test_accuracy(metadata),
            model=ModelIdentity(name=str(metadata["name"]), version=str(metadata["version"])),
            disclaimer=DISCLAIMER,
        )

    def predict_and_save(self, session: Session, inputs: AssessmentInput) -> AssessmentRecord:
        predicted_class, probability, metadata = self.model_registry.predict(inputs.canonical_features())
        assessment = self.repository.create_with_result(
            session=session, inputs=inputs, predicted_class=predicted_class,
            probability=probability, model_accuracy=_test_accuracy(metadata),
            model_name=str(metadata["name"]), model_version=str(metadata["version"]),
        )
        return assessment_to_record(assessment)


def prediction_label(predicted_class: int) -> str:
    return (
        f"Dataset class: {TARGET_POSITIVE} (research estimate)"
        if predicted_class == 1
        else f"Dataset class: {TARGET_NEGATIVE} (research estimate)"
    )


def _test_accuracy(metadata: dict) -> float | None:
    metrics = metadata.get("test_metrics", {})
    accuracy = metrics.get("accuracy") if isinstance(metrics, dict) else None
    return float(accuracy) if isinstance(accuracy, (int, float)) else None


def assessment_to_record(assessment: Assessment) -> AssessmentRecord:
    if assessment.result is None:
        raise ValueError("Persisted assessment is missing its prediction result.")
    try:
        stored_input = json.loads(assessment.input_json) if assessment.input_json else None
    except (TypeError, json.JSONDecodeError):
        stored_input = None
    # Older records are returned with their original legacy fields instead of being
    # silently represented as if they were entered using the replacement dataset.
    if stored_input is None:
        stored_input = {
            "legacy_schema": "pima-tabular-v1",
            "pregnancies": assessment.pregnancies,
            "glucose": assessment.glucose,
            "blood_pressure": assessment.blood_pressure,
            "skin_thickness": assessment.skin_thickness,
            "insulin": assessment.insulin,
            "bmi": assessment.bmi,
            "diabetes_pedigree_function": assessment.diabetes_pedigree_function,
            "age": assessment.age,
        }
    try:
        response_metadata = json.loads(assessment.result.response_metadata or "{}")
    except (TypeError, json.JSONDecodeError):
        response_metadata = {}
    return AssessmentRecord(
        prediction_id=assessment.id,
        predicted_class=assessment.result.predicted_class,
        prediction_label=prediction_label(assessment.result.predicted_class),
        model_accuracy=response_metadata.get("model_accuracy"),
        probability=assessment.result.probability,
        model=ModelIdentity(name=assessment.result.model_name, version=assessment.result.model_version),
        disclaimer=DISCLAIMER,
        created_at=assessment.created_at,
        source=assessment.source,
        input=stored_input,
    )
