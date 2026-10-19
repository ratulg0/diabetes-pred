from __future__ import annotations

import json
from uuid import uuid4

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Assessment, PredictionResult
from app.schemas.assessments import AssessmentInput


class AssessmentRepository:
    def create_with_result(
        self,
        session: Session,
        inputs: AssessmentInput,
        predicted_class: int,
        probability: float | None,
        model_accuracy: float | None,
        model_name: str,
        model_version: str,
    ) -> Assessment:
        assessment = Assessment(id=str(uuid4()), schema_version="pima-tabular-v1", **inputs.model_dump())
        result = PredictionResult(
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

    def list(self, session: Session, offset: int, limit: int, predicted_class: int | None, search: str | None = None) -> tuple[list[Assessment], int]:
        statement: Select[tuple[Assessment]] = select(Assessment).options(joinedload(Assessment.result)).order_by(Assessment.created_at.desc())
        count_statement = select(func.count(Assessment.id))
        if predicted_class is not None:
            statement = statement.join(Assessment.result).where(PredictionResult.predicted_class == predicted_class)
            count_statement = count_statement.join(PredictionResult).where(PredictionResult.predicted_class == predicted_class)
        if search:
            statement = statement.where(Assessment.id.contains(search))
            count_statement = count_statement.where(Assessment.id.contains(search))
        items = list(session.scalars(statement.offset(offset).limit(limit)).unique())
        total = int(session.scalar(count_statement) or 0)
        return items, total

    def get(self, session: Session, assessment_id: str) -> Assessment | None:
        statement = select(Assessment).options(joinedload(Assessment.result)).where(Assessment.id == assessment_id)
        return session.scalar(statement)

    def delete(self, session: Session, assessment: Assessment) -> None:
        try:
            session.delete(assessment)
            session.commit()
        except Exception:
            session.rollback()
            raise

    def count(self, session: Session) -> int:
        return int(session.scalar(select(func.count(Assessment.id))) or 0)

    def count_by_class(self, session: Session, predicted_class: int) -> int:
        statement = select(func.count(PredictionResult.id)).where(PredictionResult.predicted_class == predicted_class)
        return int(session.scalar(statement) or 0)
