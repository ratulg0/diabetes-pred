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
# Binary indicator columns produced by the preprocessing pipeline, one per
# candidate-missing feature, recording whether the original value was zero.
MISSING_INDICATOR_FEATURES: tuple[str, ...] = tuple(
    f"{feature}_was_missing" for feature in ZERO_AS_MISSING_FEATURES
)
# Engineered features added on top of the raw tabular features.
ENGINEERED_FEATURES: tuple[str, ...] = (
    "BMI_x_Age",
    "Glucose_over_BMI",
    "Pregnancies_over_Age",
    "Age_bin",
)
# Full feature vector presented to each model (raw + engineered).
MODEL_FEATURES: tuple[str, ...] = (*FEATURES, *ENGINEERED_FEATURES)
EXPECTED_COLUMNS = (*FEATURES, TARGET)
SCHEMA_VERSION = "pima-tabular-v2"
DISCLAIMER = "Research prototype only; not a diagnosis or medical advice."
