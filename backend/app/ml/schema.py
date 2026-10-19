from __future__ import annotations

FEATURES: tuple[str, ...] = (
    "Pregnancies",
    "Glucose",
    "BloodPressure",
    "SkinThickness",
    "Insulin",
    "BMI",
    "DiabetesPedigreeFunction",
    "Age",
)
TARGET = "Outcome"
ZERO_AS_MISSING_FEATURES: tuple[str, ...] = (
    "Glucose",
    "BloodPressure",
    "SkinThickness",
    "Insulin",
    "BMI",
)
EXPECTED_COLUMNS = (*FEATURES, TARGET)
SCHEMA_VERSION = "pima-tabular-v1"
DISCLAIMER = "Research prototype only; not a diagnosis or medical advice."
