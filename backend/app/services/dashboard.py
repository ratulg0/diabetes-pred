# Dashboard business service that aggregates assessment counts and recent records
# for the overview screen.
from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.assessments import AssessmentRepository
from app.schemas.dashboard import DashboardSummary
from app.services.assessments import assessment_to_record


class DashboardService:
    def __init__(self, repository: AssessmentRepository | None = None) -> None:
        self.repository = repository or AssessmentRepository()

    def summary(self, session: Session) -> DashboardSummary:
        # Pull the five most recent records plus total and class-1 counts.
        recent, _ = self.repository.list(session, offset=0, limit=5, predicted_class=None)
        return DashboardSummary(
            total_assessments=self.repository.count(session),
            higher_class_assessments=self.repository.count_by_class(session, 1),
            recent_assessments=[assessment_to_record(assessment) for assessment in recent],
        )
