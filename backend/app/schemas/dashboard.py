from __future__ import annotations

from app.schemas.assessments import AssessmentRecord

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_assessments: int
    higher_class_assessments: int
    recent_assessments: list[AssessmentRecord]
