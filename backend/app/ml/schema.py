from __future__ import annotations

# Canonical feature/target schema for the Pima-style diabetes dataset. These
# column names are the single source of truth for training, inference, and audit.
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
# Physiologic fields where a zero value is treated as candidate-missing within
# the preprocessing pipeline only; this is a modeling assumption, not fact.
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
