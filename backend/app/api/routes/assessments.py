from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_model_registry, get_session
from app.core.config import Settings
from app.ml.registry import ModelRegistry, ModelUnavailableError
from app.repositories.assessments import AssessmentRepository
from app.schemas.assessments import AssessmentInput, AssessmentPage, AssessmentRecord, PredictionResponse
from app.services.assessments import AssessmentService, assessment_to_record

router = APIRouter(prefix="/assessments", tags=["assessments"])


def service(model_registry: ModelRegistry = Depends(get_model_registry)) -> AssessmentService:
    return AssessmentService(model_registry)


@router.post("/predict", response_model=PredictionResponse)
def predict(inputs: AssessmentInput, assessment_service: AssessmentService = Depends(service)) -> PredictionResponse:
    try:
        return assessment_service.predict(inputs)
    except ModelUnavailableError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error


@router.post("", response_model=AssessmentRecord, status_code=status.HTTP_201_CREATED)
def create_assessment(
    inputs: AssessmentInput,
    session: Session = Depends(get_session),
    assessment_service: AssessmentService = Depends(service),
) -> AssessmentRecord:
    try:
        return assessment_service.predict_and_save(session, inputs)
    except ModelUnavailableError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error


@router.get("", response_model=AssessmentPage)
def list_assessments(
    session: Session = Depends(get_session),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, min_length=1, max_length=36),
    predicted_class: int | None = Query(default=None, ge=0, le=1),
) -> AssessmentPage:
    repository = AssessmentRepository()
    items, total = repository.list(session, offset=(page - 1) * page_size, limit=page_size, predicted_class=predicted_class, search=search)
    return AssessmentPage(items=[assessment_to_record(item) for item in items], page=page, page_size=page_size, total_count=total)


@router.get("/{assessment_id}", response_model=AssessmentRecord)
def get_assessment(assessment_id: str, session: Session = Depends(get_session)) -> AssessmentRecord:
    assessment = AssessmentRepository().get(session, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment was not found.")
    return assessment_to_record(assessment)


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assessment(assessment_id: str, request: Request, session: Session = Depends(get_session)) -> Response:
    settings: Settings = request.app.state.settings
    if not settings.allow_destructive_demo_actions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Deletion is disabled by local policy.")
    repository = AssessmentRepository()
    assessment = repository.get(session, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment was not found.")
    repository.delete(session, assessment)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
