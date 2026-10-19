# Ensembles: equal-weight soft voting and a stacking ensemble with a meta-learner.
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold


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


class StackingEnsemble:
    """Stacking ensemble: level-0 base pipelines + LogisticRegression meta-learner.

    Out-of-fold predictions from tuned base pipelines train the meta-learner.
    The whole stack is then wrapped in sigmoid calibration for reliable
    probabilities.
    """

    def __init__(
        self,
        base_pipelines: dict[str, Any],
        cv_folds: int = 5,
        random_seed: int = 2026,
    ) -> None:
        if len(base_pipelines) < 2:
            raise ValueError("The stacking ensemble requires at least two base models.")
        self.base_pipelines = base_pipelines
        self.cv_folds = cv_folds
        self.random_seed = random_seed
        self.stack: StackingClassifier | None = None
        self.calibrated_stack: CalibratedClassifierCV | None = None

    def fit(self, features: pd.DataFrame, target: pd.Series) -> "StackingEnsemble":
        # Fit level-0 base pipelines with out-of-fold stacking and a
        # LogisticRegression meta-learner, then calibrate the stacked output.
        cv = StratifiedKFold(
            n_splits=self.cv_folds, shuffle=True, random_state=self.random_seed
        )
        self.stack = StackingClassifier(
            estimators=list(self.base_pipelines.items()),
            final_estimator=LogisticRegression(
                max_iter=2000, random_state=self.random_seed
            ),
            cv=cv,
            stack_method="predict_proba",
            n_jobs=1,
            passthrough=False,
        )
        self.stack.fit(features, target)
        self.calibrated_stack = CalibratedClassifierCV(
            estimator=self.stack, method="sigmoid", cv=self.cv_folds
        )
        self.calibrated_stack.fit(features, target)
        return self

    def predict_proba(self, features: pd.DataFrame) -> np.ndarray:
        if self.calibrated_stack is None:
            raise RuntimeError("StackingEnsemble has not been fitted yet.")
        return np.asarray(self.calibrated_stack.predict_proba(features), dtype=float)

    def predict(self, features: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        # Classify as positive (1) when the calibrated probability >= threshold.
        return (self.predict_proba(features)[:, 1] >= threshold).astype(int)
