from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.ml.schema import DISCLAIMER


class AssessmentInput(BaseModel):
    """Input matching the replacement dataset's 14 feature columns."""
    model_config = ConfigDict(extra="forbid")

    gender: Literal["Female", "Male"]
    age: int = Field(ge=1, le=120)
    physical_activity: Literal["Low", "Moderate", "High"]
    smoking_status: Literal["Never", "Former", "Current"]
    alcohol_intake: Literal["Occasional", "Regular"] | None = None
    glucose: float | None = Field(default=None, ge=0, le=600)
    blood_pressure: float | None = Field(default=None, ge=0, le=300)
    skin_thickness: float | None = Field(default=None, ge=0, le=150)
    insulin: float | None = Field(default=None, ge=0, le=3000)
    bmi: float | None = Field(default=None, ge=0, le=100)
    cholesterol: float | None = Field(default=None, ge=0, le=1000)
    diabetes_pedigree_function: float | None = Field(default=None, ge=0, le=10)
    family_history: Literal["No", "Yes"]
    hypertension: Literal["No", "Yes"]

    @field_validator("gender", "physical_activity", "smoking_status", "alcohol_intake", "family_history", "hypertension")
    @classmethod
    def normalize_categories(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    def canonical_features(self) -> dict[str, Any]:
        return {
            "Gender": self.gender,
            "Age": self.age,
            "Physical Activity": self.physical_activity,
            "Smoking Status": self.smoking_status,
            "Alcohol Intake": self.alcohol_intake,
            "Glucose": self.glucose,
            "Blood Pressure": self.blood_pressure,
            "Skin Thickness": self.skin_thickness,
            "Insulin": self.insulin,
            "BMI": self.bmi,
            "Cholesterol": self.cholesterol,
            "Diabetes Pedigree Function": self.diabetes_pedigree_function,
            "Family History": self.family_history,
            "Hypertension": self.hypertension,
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
    input: dict[str, Any]


class AssessmentPage(BaseModel):
    items: list[AssessmentRecord]
    page: int
    page_size: int
    total_count: int
