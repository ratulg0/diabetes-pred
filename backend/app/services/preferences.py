# Business service for reading and updating local development display
# preferences (glucose unit, compact tables, assessment notifications).
from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.preferences import PreferencesRepository
from app.schemas.preferences import PreferencesResponse, PreferencesUpdate

LOCAL_DEVELOPMENT_SCOPE = "local-development"


class PreferencesService:
    def __init__(self, repository: PreferencesRepository | None = None) -> None:
        self.repository = repository or PreferencesRepository()

    def get(self, session: Session) -> PreferencesResponse:
        # Return the single local-development preference row, creating it if absent.
        preference = self.repository.get_or_create(session, LOCAL_DEVELOPMENT_SCOPE)
        return PreferencesResponse(
            scope=preference.scope,
            glucose_unit=preference.glucose_unit,
            compact_tables=preference.compact_tables,
            assessment_notifications=preference.assessment_notifications,
        )

    def update(self, session: Session, values: PreferencesUpdate) -> PreferencesResponse:
        # Update the existing preference row in place and return the new values.
        preference = self.repository.get_or_create(session, LOCAL_DEVELOPMENT_SCOPE)
        preference = self.repository.update(session, preference, **values.model_dump())
        return PreferencesResponse(scope=preference.scope, **values.model_dump())
