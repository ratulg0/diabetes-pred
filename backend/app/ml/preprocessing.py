# Preprocessing pipeline construction. Replaces physiologic zeros with missing,
# median-imputes inside each CV fold, and optionally standardizes for logistic regression.
from __future__ import annotations

import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

from app.ml.schema import FEATURES, ZERO_AS_MISSING_FEATURES


def replace_candidate_missing_zeros(frame: pd.DataFrame) -> pd.DataFrame:
    # Replace only documented candidate-missing physiologic zeros inside a fitted pipeline.
    copied = frame.loc[:, list(FEATURES)].astype(float).copy()
    for feature in ZERO_AS_MISSING_FEATURES:
        copied[feature] = copied[feature].mask(copied[feature].eq(0))
    return copied


def build_preprocessor(scale: bool) -> Pipeline:
    # Build a leakage-safe preprocessing pipeline: zero-to-missing, median
    # imputation, and optional standardization.
    steps: list[tuple[str, object]] = [
        ("candidate_zero_to_missing", FunctionTransformer(replace_candidate_missing_zeros, validate=False)),
        ("imputer", SimpleImputer(strategy="median")),
    ]
    if scale:
        steps.append(("scaler", StandardScaler()))
    return Pipeline(steps)
