# Pydantic schemas for local development display preferences (glucose unit,
# compact tables, assessment notifications). Kept separate from auth since no
# authentication exists in this research prototype.
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class PreferencesUpdate(BaseModel):
    """Writable subset of preferences a user may change."""
    glucose_unit: Literal["mg/dL", "mmol/L"]
    compact_tables: bool
    assessment_notifications: bool


class PreferencesResponse(PreferencesUpdate):
    """Preferences payload including the scope identifier."""
    scope: str
