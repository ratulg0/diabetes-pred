from __future__ import annotations

import hashlib
import json
import platform
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from app.ml.data_audit import audit_dataset, dataset_sha256
from app.ml.evaluate import evaluate_binary_classifier
from app.ml.preprocessing import build_preprocessor
from app.ml.schema import FEATURES, SCHEMA_VERSION, TARGET

RANDOM_SEED = 2026
CV_FOLDS = 5


@dataclass(frozen=True)
class CandidateResult:
    name: str
    cv_accuracy_mean: float
    cv_accuracy_std: float
    cv_roc_auc_mean: float
    cv_roc_auc_std: float
    cv_brier_mean: float
    cv_brier_std: float


def candidate_pipelines() -> dict[str, Pipeline]:
    """Return fresh, leakage-safe pipelines for all required benchmark candidates."""
    return {
        "logistic_regression": Pipeline(
            [("preprocessor", build_preprocessor(scale=True)), ("estimator", LogisticRegression(max_iter=2000, random_state=RANDOM_SEED))]
        ),
        "random_forest": Pipeline(
            [("preprocessor", build_preprocessor(scale=False)), ("estimator", RandomForestClassifier(n_estimators=300, max_depth=6, min_samples_leaf=4, class_weight="balanced", random_state=RANDOM_SEED, n_jobs=-1))]
        ),
        "xgboost": Pipeline(
            [("preprocessor", build_preprocessor(scale=False)), ("estimator", XGBClassifier(n_estimators=200, max_depth=3, learning_rate=0.04, subsample=0.8, colsample_bytree=0.8, reg_lambda=2.0, eval_metric="logloss", random_state=RANDOM_SEED, n_jobs=1))]
        ),
        "hist_gradient_boosting": Pipeline(
            [("preprocessor", build_preprocessor(scale=False)), ("estimator", HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, l2_regularization=1.0, random_state=RANDOM_SEED))]
        ),
    }


def train_and_select(dataset_path: Path, artifact_path: Path, version: str | None = None) -> dict[str, Any]:
    """Benchmark candidates, select by training-CV ROC-AUC, then persist one trusted artifact."""
    audit = audit_dataset(dataset_path)
    if not audit.schema_matches_expected:
        raise ValueError("Dataset schema does not exactly match the required tabular classification schema.")
    frame = pd.read_csv(dataset_path)
    features = frame.loc[:, list(FEATURES)]
    target = frame[TARGET]
    if set(target.unique()) - {0, 1}:
        raise ValueError("Outcome must contain only binary values 0 and 1.")
    train_features, test_features, train_target, test_target = train_test_split(
        features, target, test_size=0.2, stratify=target, random_state=RANDOM_SEED
    )
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_SEED)
    results: list[CandidateResult] = []
    for name, pipeline in candidate_pipelines().items():
        scores = cross_validate(
            pipeline,
            train_features,
            train_target,
            cv=cv,
            scoring={"accuracy": "accuracy", "roc_auc": "roc_auc", "brier": "neg_brier_score"},
            n_jobs=1,
            return_train_score=False,
        )
        results.append(
            CandidateResult(
                name=name,
                cv_accuracy_mean=round(float(np.mean(scores["test_accuracy"])), 6),
                cv_accuracy_std=round(float(np.std(scores["test_accuracy"], ddof=1)), 6),
                cv_roc_auc_mean=round(float(np.mean(scores["test_roc_auc"])), 6),
                cv_roc_auc_std=round(float(np.std(scores["test_roc_auc"], ddof=1)), 6),
                cv_brier_mean=round(float(-np.mean(scores["test_brier"])), 6),
                cv_brier_std=round(float(np.std(-scores["test_brier"], ddof=1)), 6),
            )
        )
    # Selection is fixed before reading the held-out test set: highest CV ROC-AUC, then lower Brier score, then name.
    selected = sorted(results, key=lambda item: (-item.cv_roc_auc_mean, item.cv_brier_mean, item.name))[0]
    selected_pipeline = candidate_pipelines()[selected.name]
    # Fit calibration only on the training partition after the candidate is selected.
    pipeline = CalibratedClassifierCV(estimator=selected_pipeline, method="sigmoid", cv=CV_FOLDS)
    pipeline.fit(train_features, train_target)
    test_probabilities = pipeline.predict_proba(test_features)[:, 1]
    test_metrics = evaluate_binary_classifier(test_target, test_probabilities)
    generated_version = version or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    metadata: dict[str, Any] = {
        "name": selected.name,
        "version": generated_version,
        "algorithm": type(selected_pipeline.named_steps["estimator"]).__name__,
        "feature_schema": list(FEATURES),
        "schema_version": SCHEMA_VERSION,
        "dataset_sha256": dataset_sha256(dataset_path),
        "dataset_file_name": dataset_path.name,
        "audit": audit.to_dict(),
        "candidate_results": [asdict(result) for result in results],
        "selection_rule": "Highest 5-fold stratified training-set CV ROC-AUC; ties use lower CV Brier score, then model name. The held-out test set is evaluated only after selection.",
        "test_metrics": test_metrics,
        "split": {"random_seed": RANDOM_SEED, "test_fraction": 0.2, "test_rows": int(len(test_target)), "training_rows": int(len(train_target)), "cv_folds": CV_FOLDS},
        "preprocessing": "Replace candidate-missing zero values only for Glucose, BloodPressure, SkinThickness, Insulin, and BMI; median impute inside each fold; standardize only logistic regression.",
        "probability_calibrated": True,
        "calibration": {"method": "sigmoid", "cv_folds": CV_FOLDS, "scope": "training partition only"},
        "trained_at_utc": datetime.now(UTC).isoformat(),
        "dependency_versions": {"python": platform.python_version(), "scikit_learn": sklearn.__version__, "xgboost": xgboost.__version__},
    }
    package = {"pipeline": pipeline, "metadata": metadata}
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = artifact_path.with_suffix(".tmp")
    joblib.dump(package, temporary_path)
    temporary_path.replace(artifact_path)
    metadata["artifact_sha256"] = _file_sha256(artifact_path)
    metadata_path = artifact_path.with_suffix(".metadata.json")
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return metadata


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
