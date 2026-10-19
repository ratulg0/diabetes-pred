from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class PreferencesUpdate(BaseModel):
    glucose_unit: Literal["mg/dL", "mmol/L"]
    compact_tables: bool
    assessment_notifications: bool


class PreferencesResponse(PreferencesUpdate):
    scope: str
