# Preprocessing pipeline construction. Replaces physiologic zeros with missing,
# appends missingness indicator columns, adds engineered features, median-imputes
# with IterativeImputer (MICE) inside each CV fold, and optionally standardizes
# for logistic regression. All steps run inside the scikit-learn Pipeline so no
# statistics leak across train/validation folds.
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.experimental import enable_iterative_imputer  # noqa: F401  (enables IterativeImputer)
from sklearn.impute import IterativeImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

from app.ml.schema import (
    ENGINEERED_FEATURES,
    FEATURES,
    MISSING_INDICATOR_FEATURES,
    MODEL_FEATURES,
    ZERO_AS_MISSING_FEATURES,
)


def add_engineered_features(frame: pd.DataFrame) -> pd.DataFrame:
    # Derive interaction, ratio, and binned features from the raw Pima columns.
    copied = frame.loc[:, list(FEATURES)].astype(float).copy()
    age = copied["Age"].replace(0, np.nan)
    bmi = copied["BMI"]
    copied["BMI_x_Age"] = bmi * copied["Age"]
    copied["Glucose_over_BMI"] = copied["Glucose"] / bmi.replace(0, np.nan)
    copied["Pregnancies_over_Age"] = copied["Pregnancies"] / age
    copied["Age_bin"] = pd.cut(
        copied["Age"], bins=[0, 30, 45, 60, 120], labels=[0, 1, 2, 3]
    ).astype(float)
    return copied.loc[:, list(MODEL_FEATURES)]


def add_missingness_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    # Append one binary indicator per candidate-missing feature before imputation
    # so models can learn that "recorded as zero" is itself a signal.
    copied = frame.copy()
    for feature in ZERO_AS_MISSING_FEATURES:
        copied[f"{feature}_was_missing"] = frame[feature].eq(0).astype(float)
    return copied


def build_preprocessor(scale: bool) -> Pipeline:
    # Build a leakage-safe preprocessing pipeline:
    #   engineered features -> missingness indicators -> IterativeImputer (MICE)
    #   -> optional StandardScaler
    steps: list[tuple[str, object]] = [
        (
            "engineered_features",
            FunctionTransformer(add_engineered_features, validate=False),
        ),
        (
            "missingness_indicators",
            FunctionTransformer(add_missingness_indicators, validate=False),
        ),
        (
            "imputer",
            IterativeImputer(random_state=RANDOM_SEED, sample_posterior=False),
        ),
    ]
    if scale:
        steps.append(("scaler", StandardScaler()))
    preprocessor = Pipeline(steps)
    preprocessor.set_output(transform="pandas")
    return preprocessor


# Shared seed so MICE imputation is deterministic across runs.
RANDOM_SEED = 2026
