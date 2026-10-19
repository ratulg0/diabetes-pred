"""Request/response schemas for the uploaded 20k-row dataset model."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

from app.ml.uploaded_dataset import DISCLAIMER


class DatasetAssessmentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gender: Literal["Male", "Female"]
    age: int = Field(ge=1, le=120)
    physical_activity: Literal["Low", "Moderate", "High"]
    smoking_status: Literal["Never", "Former", "Current"]
    alcohol_intake: Literal["Occasional", "Regular"]
    glucose: float = Field(ge=0, le=500)
    blood_pressure: float = Field(ge=0, le=300)
    skin_thickness: float = Field(ge=0, le=150)
    insulin: float = Field(ge=0, le=2000)
    bmi: float = Field(gt=0, le=100)
    cholesterol: float = Field(ge=0, le=1000)
    diabetes_pedigree_function: float = Field(ge=0, le=10)
    family_history: Literal["Yes", "No"]
    hypertension: Literal["Yes", "No"]

    def to_features(self) -> dict[str, str | int | float]:
        return {
            "Gender": self.gender, "Age": self.age,
            "Physical Activity": self.physical_activity,
            "Smoking Status": self.smoking_status, "Alcohol Intake": self.alcohol_intake,
            "Glucose": self.glucose, "Blood Pressure": self.blood_pressure,
            "Skin Thickness": self.skin_thickness, "Insulin": self.insulin,
            "BMI": self.bmi, "Cholesterol": self.cholesterol,
            "Diabetes Pedigree Function": self.diabetes_pedigree_function,
            "Family History": self.family_history, "Hypertension": self.hypertension,
        }


class DatasetPredictionResponse(BaseModel):
    prediction_label: Literal["Diabetic", "Non-diabetic"]
    probability: float = Field(ge=0, le=1)
    model_name: str
    metrics: dict[str, float | str]
    disclaimer: str = DISCLAIMER
