# Persistence operations for lifestyle assessments and prediction results.
from __future__ import annotations

import json
from uuid import uuid4

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import LifestyleAssessment, LifestylePredictionResult
from app.schemas.lifestyle_assessments import LifestyleAssessmentInput


class LifestyleAssessmentRepository:
    def create_with_result(
        self,
        session: Session,
        inputs: LifestyleAssessmentInput,
        predicted_class: int,
        probability: float | None,
        model_accuracy: float | None,
        model_name: str,
        model_version: str,
    ) -> LifestyleAssessment:
        # Insert one lifestyle assessment row plus one linked prediction result
        # atomically, rolling back on any failure.
        assessment = LifestyleAssessment(id=str(uuid4()), schema_version="uci-cdc-diabetes-health-indicators-v1", **inputs.model_dump())
        result = LifestylePredictionResult(
            id=str(uuid4()),
            predicted_class=predicted_class,
            probability=probability,
            model_name=model_name,
            model_version=model_version,
            response_metadata=json.dumps({"probability_calibrated": probability is not None, "model_accuracy": model_accuracy}),
        )
        assessment.result = result
        try:
            session.add(assessment)
            session.commit()
        except Exception:
            session.rollback()
            raise
        session.refresh(assessment)
        return assessment

    def list(
        self,
        session: Session,
        offset: int,
        limit: int,
        predicted_class: int | None,
        search: str | None = None,
    ) -> tuple[list[LifestyleAssessment], int]:
        # Return paginated lifestyle assessment rows (eagerly loading results),
        # optionally filtered by predicted class or ID substring, plus total count.
        statement: Select[tuple[LifestyleAssessment]] = (
            select(LifestyleAssessment)
            .options(joinedload(LifestyleAssessment.result))
            .order_by(LifestyleAssessment.created_at.desc())
        )
        count_statement = select(func.count(LifestyleAssessment.id))
        if predicted_class is not None:
            statement = statement.join(LifestyleAssessment.result).where(LifestylePredictionResult.predicted_class == predicted_class)
            count_statement = count_statement.join(LifestylePredictionResult).where(LifestylePredictionResult.predicted_class == predicted_class)
        if search:
            statement = statement.where(LifestyleAssessment.id.contains(search))
            count_statement = count_statement.where(LifestyleAssessment.id.contains(search))
        items = list(session.scalars(statement.offset(offset).limit(limit)).unique())
        total = int(session.scalar(count_statement) or 0)
        return items, total

    def get(self, session: Session, assessment_id: str) -> LifestyleAssessment | None:
        # Fetch a single lifestyle assessment by ID with its result eager-loaded.
        statement = select(LifestyleAssessment).options(joinedload(LifestyleAssessment.result)).where(LifestyleAssessment.id == assessment_id)
        return session.scalar(statement)

    def delete(self, session: Session, assessment: LifestyleAssessment) -> None:
        # Delete a lifestyle assessment row, rolling back on failure.
        try:
            session.delete(assessment)
            session.commit()
        except Exception:
            session.rollback()
            raise

    def count(self, session: Session) -> int:
        # Total number of stored lifestyle assessment rows.
        return int(session.scalar(select(func.count(LifestyleAssessment.id))) or 0)

    def count_by_class(self, session: Session, predicted_class: int) -> int:
        # Count prediction results matching the given class (0 or 1).
        statement = select(func.count(LifestylePredictionResult.id)).where(LifestylePredictionResult.predicted_class == predicted_class)
        return int(session.scalar(statement) or 0)
