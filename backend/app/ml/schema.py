from __future__ import annotations

# GlucoCare clinical-assessment schema for the replacement 20,000-row dataset.
# This dataset is a research/educational source and is not clinically validated.
FEATURES: tuple[str, ...] = (
    "Gender",
    "Age",
    "Physical Activity",
    "Smoking Status",
    "Alcohol Intake",
    "Glucose",
    "Blood Pressure",
    "Skin Thickness",
    "Insulin",
    "BMI",
    "Cholesterol",
    "Diabetes Pedigree Function",
    "Family History",
    "Hypertension",
)
CATEGORICAL_FEATURES: tuple[str, ...] = (
    "Gender",
    "Physical Activity",
    "Smoking Status",
    "Alcohol Intake",
    "Family History",
    "Hypertension",
)
NUMERIC_FEATURES: tuple[str, ...] = tuple(
    feature for feature in FEATURES if feature not in CATEGORICAL_FEATURES
)
TARGET = "Outcome"
TARGET_POSITIVE = "Diabetic"
TARGET_NEGATIVE = "Non-diabetic"
EXPECTED_COLUMNS = (*FEATURES, TARGET)
SCHEMA_VERSION = "glucocare-clinical-dataset-v1"
DISCLAIMER = (
    "Research prototype only. This estimate is not a diagnosis, does not replace "
    "laboratory testing or a clinician, and must not guide treatment decisions."
)
