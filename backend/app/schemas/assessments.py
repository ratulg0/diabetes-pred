from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.ml.schema import DISCLAIMER


class AssessmentInput(BaseModel):
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
    prediction_id: str
    predicted_class: int = Field(ge=0, le=1)
    prediction_label: str
    probability: float | None = Field(default=None, ge=0, le=1)
    model_accuracy: float | None = Field(default=None, ge=0, le=1)
    model: ModelIdentity
    disclaimer: str = DISCLAIMER


class AssessmentRecord(PredictionResponse):
    created_at: datetime
    source: str
    input: AssessmentInput


class AssessmentPage(BaseModel):
    items: list[AssessmentRecord]
    page: int
    page_size: int
    total_count: int
