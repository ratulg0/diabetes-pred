# Preferences routes: read and update local development display settings.
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_session
from app.schemas.preferences import PreferencesResponse, PreferencesUpdate
from app.services.preferences import PreferencesService

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("", response_model=PreferencesResponse)
def get_preferences(session: Session = Depends(get_session)) -> PreferencesResponse:
    # Return the local-development preference row, creating defaults if absent.
    return PreferencesService().get(session)


@router.put("", response_model=PreferencesResponse)
def update_preferences(values: PreferencesUpdate, session: Session = Depends(get_session)) -> PreferencesResponse:
    # Persist updated display preferences and return the new values.
    return PreferencesService().update(session, values)
