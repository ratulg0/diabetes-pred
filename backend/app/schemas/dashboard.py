# Schema for the dashboard summary payload returned to the frontend, composed
# of assessment counts and the five most recent records.
from __future__ import annotations

from app.schemas.assessments import AssessmentRecord

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    """Aggregated dashboard statistics and recent activity."""
    total_assessments: int
    higher_class_assessments: int
    recent_assessments: list[AssessmentRecord]
