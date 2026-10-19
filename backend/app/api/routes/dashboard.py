# Dashboard route returning aggregated assessment counts and recent records.
from __future__ import annotations

import csv
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_session
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def summary(session: Session = Depends(get_session)) -> DashboardSummary:
    # Delegate to DashboardService for total/class counts and recent records.
    return DashboardService().summary(session)


@router.get("/dataset-distribution")
def dataset_distribution(request: Request) -> dict[str, object]:
    """Return aggregated counts for the source dataset Outcome column."""
    dataset_path = request.app.state.settings.dataset_path
    if not dataset_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Clinical dataset is missing: {dataset_path}",
        )

    counts: Counter[str] = Counter()
    row_count = 0
    try:
        with dataset_path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            if not reader.fieldnames or "Outcome" not in reader.fieldnames:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="The clinical dataset must contain an Outcome column.",
                )
            for row in reader:
                row_count += 1
                outcome = (row.get("Outcome") or "").strip()
                counts[outcome if outcome else "Missing"] += 1
    except UnicodeDecodeError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The clinical dataset could not be decoded as UTF-8.",
        ) from error

    preferred_order = ["Non-diabetic", "Diabetic", "Missing"]
    labels = [label for label in preferred_order if label in counts]
    labels.extend(sorted(label for label in counts if label not in preferred_order))
    return {
        "column": "Outcome",
        "row_count": row_count,
        "counts": [{"label": label, "count": counts[label]} for label in labels],
    }
