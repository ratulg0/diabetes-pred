# Persistence operations for user preferences. Encapsulates get-or-create and
# update logic for the single local-development preference row.
from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import UserPreference


class PreferencesRepository:
    def get_or_create(self, session: Session, scope: str) -> UserPreference:
        # Return the existing preference row for a scope, inserting defaults if absent.
        preference = session.scalar(select(UserPreference).where(UserPreference.scope == scope))
        if preference is not None:
            return preference
        preference = UserPreference(id=str(uuid4()), scope=scope)
        try:
            session.add(preference)
            session.commit()
        except Exception:
            session.rollback()
            raise
        session.refresh(preference)
        return preference

    def update(self, session: Session, preference: UserPreference, **values: object) -> UserPreference:
        # Apply supplied field changes to the preference row and persist.
        for key, value in values.items():
            setattr(preference, key, value)
        try:
            session.commit()
        except Exception:
            session.rollback()
            raise
        session.refresh(preference)
        return preference
