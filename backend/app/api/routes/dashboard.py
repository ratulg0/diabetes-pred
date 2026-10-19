# Dashboard route returning aggregated assessment counts and recent records.
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_session
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def summary(session: Session = Depends(get_session)) -> DashboardSummary:
    # Delegate to DashboardService for total/class counts and recent records.
    return DashboardService().summary(session)
