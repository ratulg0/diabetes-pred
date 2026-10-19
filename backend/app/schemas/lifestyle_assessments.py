# Request/response schemas for the lifestyle assessments feature.
from __future__ import annotations

from datetime import datetime

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from app.ml.schema import DISCLAIMER


class LifestyleAssessmentInput(BaseModel):
    """CDC Diabetes Health Indicators survey feature vector (21 indicators)."""
    model_config = ConfigDict(extra="forbid")

    high_bp: int = Field(ge=0, le=1)
    high_chol: int = Field(ge=0, le=1)
    chol_check: int = Field(ge=0, le=1)
    bmi: float = Field(ge=10, le=100)
    smoker: int = Field(ge=0, le=1)
    stroke: int = Field(ge=0, le=1)
    heart_disease_or_attack: int = Field(ge=0, le=1)
    phys_activity: int = Field(ge=0, le=1)
    fruits: int = Field(ge=0, le=1)
    veggies: int = Field(ge=0, le=1)
    hvy_alcohol_consump: int = Field(ge=0, le=1)
    any_healthcare: int = Field(ge=0, le=1)
    no_docbc_cost: int = Field(ge=0, le=1)
    gen_hlth: int = Field(ge=1, le=5)
    ment_hlth: int = Field(ge=0, le=30)
    phys_hlth: int = Field(ge=0, le=30)
    diff_walk: int = Field(ge=0, le=1)
    sex: int = Field(ge=0, le=1)
    age: int = Field(ge=1, le=13)
    education: int = Field(ge=1, le=6)
    income: int = Field(ge=1, le=8)

    def canonical_features(self) -> dict[str, float | int]:
        """Map snake_case inputs to the dataset column names the model expects."""
        return {
            "HighBP": self.high_bp,
            "HighChol": self.high_chol,
            "CholCheck": self.chol_check,
            "BMI": self.bmi,
            "Smoker": self.smoker,
            "Stroke": self.stroke,
            "HeartDiseaseorAttack": self.heart_disease_or_attack,
            "PhysActivity": self.phys_activity,
            "Fruits": self.fruits,
            "Veggies": self.veggies,
            "HvyAlcoholConsump": self.hvy_alcohol_consump,
            "AnyHealthcare": self.any_healthcare,
            "NoDocbcCost": self.no_docbc_cost,
            "GenHlth": self.gen_hlth,
            "MentHlth": self.ment_hlth,
            "PhysHlth": self.phys_hlth,
            "DiffWalk": self.diff_walk,
            "Sex": self.sex,
            "Age": self.age,
            "Education": self.education,
            "Income": self.income,
        }

    def feature_frame(self) -> pd.DataFrame:
        """Return a single-row DataFrame ordered as the model expects."""
        return pd.DataFrame([self.canonical_features()])


class ModelIdentity(BaseModel):
    name: str
    version: str


class LifestylePredictionResponse(BaseModel):
    """Model output returned for lifestyle predict endpoint."""
    prediction_id: str
    predicted_class: int = Field(ge=0, le=1)
    prediction_label: str
    probability: float | None = Field(default=None, ge=0, le=1)
    model_accuracy: float | None = Field(default=None, ge=0, le=1)
    model: ModelIdentity
    target_definition: str
    disclaimer: str = DISCLAIMER


class LifestyleAssessmentRecord(LifestylePredictionResponse):
    """Persisted lifestyle assessment including timestamp and original inputs."""
    created_at: datetime
    source: str
    input: LifestyleAssessmentInput


class LifestyleAssessmentPage(BaseModel):
    """Paginated list of lifestyle assessment records with total count."""
    items: list[LifestyleAssessmentRecord]
    page: int
    page_size: int
    total_count: int
