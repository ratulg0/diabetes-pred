# Soft-voting ensemble that averages calibrated probabilities across member models.
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class SoftVotingEnsemble:
    """Average class probabilities from each calibrated member model."""

    def __init__(self, estimators: dict[str, Any]) -> None:
        # Require at least two models so voting is meaningful.
        if len(estimators) < 2:
            raise ValueError("The ensemble requires at least two trained models.")
        self.estimators = estimators

    def predict_proba(self, features: pd.DataFrame) -> np.ndarray:
        # Average positive-class probabilities across all calibrated members and
        # renormalize rows so they sum to one.
        probabilities = [
            np.asarray(model.predict_proba(features), dtype=float)
            for model in self.estimators.values()
        ]
        averaged = np.mean(probabilities, axis=0)
        row_sums = averaged.sum(axis=1, keepdims=True)
        return averaged / np.where(row_sums == 0, 1, row_sums)

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        # Classify as positive (1) when the averaged probability is >= 0.5.
        return (self.predict_proba(features)[:, 1] >= 0.5).astype(int)
