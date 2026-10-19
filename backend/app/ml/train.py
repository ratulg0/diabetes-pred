from __future__ import annotations

import hashlib
import json
import platform
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import average_precision_score, brier_score_loss, confusion_matrix, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline

from app.ml.data_audit import audit_dataset, dataset_sha256
from app.ml.preprocessing import build_preprocessor
from app.ml.schema import FEATURES, SCHEMA_VERSION, TARGET, TARGET_NEGATIVE, TARGET_POSITIVE


RANDOM_SEED = 2026


def candidate_pipelines() -> dict[str, Any]:
    """Candidate estimator factories retained for API/model-registry compatibility."""
    return {
        "random_forest": RandomForestClassifier(n_estimators=300, class_weight="balanced", random_state=RANDOM_SEED, n_jobs=-1),
        "extra_trees": ExtraTreesClassifier(n_estimators=300, class_weight="balanced", random_state=RANDOM_SEED, n_jobs=-1),
    }


def _pipeline(estimator: Any) -> Pipeline:
    return Pipeline([("preprocessor", build_preprocessor()), ("estimator", estimator)])


def train_and_select(dataset_path: Path, artifact_path: Path, version: str | None = None) -> dict[str, Any]:
    """Train and evaluate a leakage-safe model using the replacement dataset."""
    audit = audit_dataset(dataset_path)
    if not audit.schema_matches_expected:
        raise ValueError(
            "Clinical dataset schema mismatch. Expected exactly: " + ", ".join((*FEATURES, TARGET))
        )
    frame = pd.read_csv(dataset_path)
    frame = frame.dropna(subset=[TARGET]).copy()
    labels = frame[TARGET].astype(str).str.strip()
    unknown = set(labels.unique()) - {TARGET_POSITIVE, TARGET_NEGATIVE}
    if unknown:
        raise ValueError(f"Unexpected Outcome labels: {sorted(unknown)}")
    X = frame.loc[:, list(FEATURES)]
    y = (labels == TARGET_POSITIVE).astype(int)
    if y.nunique() != 2:
        raise ValueError("Outcome must contain both Diabetic and Non-diabetic classes.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_SEED
    )
    candidates = candidate_pipelines()
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    candidate_results: list[dict[str, Any]] = []
    fitted: list[tuple[float, str, Pipeline]] = []
    for name, estimator in candidates.items():
        model = _pipeline(estimator)
        scores = cross_validate(
            model, X_train, y_train, cv=cv, scoring={"roc_auc": "roc_auc", "f1": "f1", "accuracy": "accuracy"},
            n_jobs=1, error_score="raise",
        )
        result = {
            "name": name,
            "cv_accuracy_mean": round(float(np.mean(scores["test_accuracy"])), 5),
            "cv_f1_mean": round(float(np.mean(scores["test_f1"])), 5),
            "cv_roc_auc_mean": round(float(np.mean(scores["test_roc_auc"])), 5),
        }
        candidate_results.append(result)
        fitted.append((result["cv_roc_auc_mean"], name, model))
    _, selected_name, selected_model = max(fitted, key=lambda item: item[0])
    selected_model.fit(X_train, y_train)
    probabilities = selected_model.predict_proba(X_test)[:, 1]
    threshold = 0.5
    predictions = (probabilities >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, predictions, labels=[0, 1]).ravel()
    metrics = {
        "accuracy": round(float((tp + tn) / max(tp + tn + fp + fn, 1)), 5),
        "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 5),
        "pr_auc": round(float(average_precision_score(y_test, probabilities)), 5),
        "f1": round(float(f1_score(y_test, predictions, zero_division=0)), 5),
        "brier_score": round(float(brier_score_loss(y_test, probabilities)), 5),
        "sensitivity": round(float(tp / (tp + fn)) if tp + fn else 0.0, 5),
        "specificity": round(float(tn / (tn + fp)) if tn + fp else 0.0, 5),
        "threshold": threshold,
        "true_negative": int(tn), "false_positive": int(fp),
        "false_negative": int(fn), "true_positive": int(tp),
    }
    generated_version = version or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    metadata: dict[str, Any] = {
        "name": selected_name,
        "version": generated_version,
        "algorithm": type(selected_model.named_steps["estimator"]).__name__,
        "members": [item["name"] for item in candidate_results],
        "feature_schema": list(FEATURES),
        "schema_version": SCHEMA_VERSION,
        "dataset_sha256": dataset_sha256(dataset_path),
        "dataset_file_name": dataset_path.name,
        "audit": audit.to_dict(),
        "candidate_results": candidate_results,
        "selection_rule": "Select highest mean stratified-CV ROC-AUC, then evaluate once on the held-out test split.",
        "test_metrics": metrics,
        "split": {"random_seed": RANDOM_SEED, "test_fraction": 0.2, "test_rows": int(len(y_test)), "training_rows": int(len(y_train)), "cv_folds": 5},
        "preprocessing": "Median imputation with missingness indicators for numeric features; most-frequent imputation and one-hot encoding for categorical features; all fitted within each training fold.",
        "class_balance": {TARGET_NEGATIVE: int((y == 0).sum()), TARGET_POSITIVE: int((y == 1).sum())},
        "probability_calibrated": False,
        "clinical_validation": "Not performed. Research/educational use only; not for diagnosis or treatment.",
        "trained_at_utc": datetime.now(UTC).isoformat(),
        "dependency_versions": {"python": platform.python_version(), "scikit_learn": sklearn.__version__},
    }
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = artifact_path.with_suffix(".tmp")
    joblib.dump({"pipeline": selected_model, "metadata": metadata}, temporary_path)
    temporary_path.replace(artifact_path)
    metadata["artifact_sha256"] = _file_sha256(artifact_path)
    artifact_path.with_suffix(".metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return metadata


def retrain_candidate(dataset_path: Path, artifact_path: Path, model_name: str, version: str | None = None, previous_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    candidates = candidate_pipelines()
    if model_name not in candidates:
        raise ValueError(f"Unsupported model name: {model_name}")
    # Current retraining endpoint re-runs model selection; candidate name is accepted for compatibility.
    metadata = train_and_select(dataset_path, artifact_path, version)
    metadata["requested_candidate"] = model_name
    return metadata


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
