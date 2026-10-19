# Request/response schemas for the assessments feature. AssessmentInput is the
# validated patient feature vector; PredictionResponse is the model output
# envelope; AssessmentRecord adds persistence fields on top.
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.ml.schema import DISCLAIMER


class AssessmentInput(BaseModel):
    """Patient feature vector with per-field clinical bounds; extra fields rejected."""
    model_config = ConfigDict(extra="forbid")

    pregnancies: int = Field(ge=0, le=25)
    glucose: float = Field(ge=0, le=400)
    blood_pressure: float = Field(ge=0, le=250)
    skin_thickness: float = Field(ge=0, le=150)
    insulin: float = Field(ge=0, le=1000)
    bmi: float = Field(gt=0, le=100)
    diabetes_pedigree_function: float = Field(ge=0, le=5)
    age: int = Field(ge=1, le=120)

    def canonical_features(self) -> dict[str, float | int]:
        """Map snake_case inputs to the dataset column names the model expects."""
        return {
            "Pregnancies": self.pregnancies,
            "Glucose": self.glucose,
            "BloodPressure": self.blood_pressure,
            "SkinThickness": self.skin_thickness,
            "Insulin": self.insulin,
            "BMI": self.bmi,
            "DiabetesPedigreeFunction": self.diabetes_pedigree_function,
            "Age": self.age,
        }


class ModelIdentity(BaseModel):
    name: str
    version: str


class PredictionResponse(BaseModel):
    """Model output returned for both predict and saved-assessment endpoints."""
    prediction_id: str
    predicted_class: int = Field(ge=0, le=1)
    prediction_label: str
    probability: float | None = Field(default=None, ge=0, le=1)
    model_accuracy: float | None = Field(default=None, ge=0, le=1)
    model: ModelIdentity
    disclaimer: str = DISCLAIMER


class AssessmentRecord(PredictionResponse):
    """Persisted assessment including timestamp, source, and original inputs."""
    created_at: datetime
    source: str
    input: AssessmentInput


class AssessmentPage(BaseModel):
    """Paginated list of assessment records with total count."""
    items: list[AssessmentRecord]
    page: int
    page_size: int
    total_count: int
