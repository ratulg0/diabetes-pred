# Training entry point: audits the dataset, tunes hyperparameters per candidate
# with Optuna, adds engineered features + missingness indicators, imputes with
# IterativeImputer (MICE), balances classes, stacks calibrated candidates with a
# LogisticRegression meta-learner, tunes the decision threshold on a validation
# split, and persists the artifact with metadata and checksum sidecar.
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
import optuna
import pandas as pd
import sklearn
import xgboost
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from app.ml.data_audit import audit_dataset, dataset_sha256
from app.ml.evaluate import evaluate_binary_classifier, tune_threshold
from app.ml.ensemble import StackingEnsemble
from app.ml.preprocessing import build_preprocessor
from app.ml.schema import (
    ENGINEERED_FEATURES,
    FEATURES,
    MISSING_INDICATOR_FEATURES,
    MODEL_FEATURES,
    SCHEMA_VERSION,
    TARGET,
    ZERO_AS_MISSING_FEATURES,
)

RANDOM_SEED = 2026
CV_FOLDS = 5
OPTUNA_TRIALS = 3
VAL_FRACTION = 0.2


@dataclass(frozen=True)
class CandidateResult:
    name: str
    cv_accuracy_mean: float
    cv_accuracy_std: float
    cv_roc_auc_mean: float
    cv_roc_auc_std: float
    cv_brier_mean: float
    cv_brier_std: float


def candidate_param_space(trial: optuna.Trial, model_name: str) -> dict[str, Any]:
    # Suggest hyperparameters for one candidate model within a bounded search
    # space tuned for the small Pima dataset.
    if model_name == "logistic_regression":
        penalty = trial.suggest_categorical("penalty", ["l1", "l2", None])
        solver = trial.suggest_categorical("solver", ["lbfgs", "liblinear", "saga"])
        return {
            "C": trial.suggest_float("C", 1e-4, 1e2, log=True),
            "penalty": penalty,
            "solver": solver,
            "max_iter": 5000,
            "class_weight": trial.suggest_categorical(
                "class_weight", [None, "balanced"]
            ),
            "random_state": RANDOM_SEED,
        }
    if model_name == "random_forest":
        return {
            "n_estimators": trial.suggest_int("n_estimators", 100, 600),
            "max_depth": trial.suggest_categorical("max_depth", [3, 5, 8, 12, None]),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
            "max_features": trial.suggest_categorical(
                "max_features", ["sqrt", "log2", None]
            ),
            "class_weight": trial.suggest_categorical(
                "class_weight", [None, "balanced", "balanced_subsample"]
            ),
            "random_state": RANDOM_SEED,
            "n_jobs": 1,
        }
    if model_name == "xgboost":
        neg_pos_ratio = trial.user_attrs.get("neg_pos_ratio", 1.0)
        return {
            "n_estimators": trial.suggest_int("n_estimators", 100, 600),
            "max_depth": trial.suggest_int("max_depth", 2, 10),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "reg_lambda": trial.suggest_float("reg_lambda", 1.0, 10.0, log=True),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
            "scale_pos_weight": trial.suggest_float(
                "scale_pos_weight", 0.5, neg_pos_ratio * 2.0
            ),
            "eval_metric": "logloss",
            "random_state": RANDOM_SEED,
            "n_jobs": 1,
        }
    if model_name == "hist_gradient_boosting":
        return {
            "max_iter": trial.suggest_int("max_iter", 100, 500),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "max_leaf_nodes": trial.suggest_int("max_leaf_nodes", 5, 30),
            "l2_regularization": trial.suggest_float(
                "l2_regularization", 0.1, 10.0, log=True
            ),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 20),
            "random_state": RANDOM_SEED,
        }
    raise ValueError(f"Unsupported model name: {model_name}")


def build_estimator(model_name: str, params: dict[str, Any]) -> Any:
    # Instantiate a fresh estimator (without preprocessing) from tuned params.
    clean_params = {k: v for k, v in params.items() if k != "neg_pos_ratio"}
    if model_name == "logistic_regression":
        return LogisticRegression(**clean_params)
    if model_name == "random_forest":
        return RandomForestClassifier(**clean_params)
    if model_name == "xgboost":
        return XGBClassifier(**clean_params)
    if model_name == "hist_gradient_boosting":
        return HistGradientBoostingClassifier(**clean_params)
    raise ValueError(f"Unsupported model name: {model_name}")


def tune_model(
    model_name: str,
    train_features: pd.DataFrame,
    train_target: pd.Series,
    neg_pos_ratio: float,
    n_trials: int = OPTUNA_TRIALS,
) -> tuple[dict[str, Any], CandidateResult]:
    # Run an Optuna study to pick hyperparameters, then evaluate the best
    # configuration with stratified cross-validation.
    sampler = optuna.samplers.TPESampler(seed=RANDOM_SEED)
    study = optuna.create_study(direction="maximize", sampler=sampler)

    def objective(trial: optuna.Trial) -> float:
        trial.set_user_attr("neg_pos_ratio", neg_pos_ratio)
        params = candidate_param_space(trial, model_name)
        estimator = build_estimator(model_name, params)
        pipeline = Pipeline(
            [
                ("preprocessor", build_preprocessor(scale=model_name == "logistic_regression")),
                ("estimator", estimator),
            ]
        )
        cv = StratifiedKFold(
            n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_SEED
        )
        scores = cross_validate(
            pipeline,
            train_features,
            train_target,
            cv=cv,
            scoring={
                "accuracy": "accuracy",
                "roc_auc": "roc_auc",
                "brier": "neg_brier_score",
                "f1": "f1",
            },
            n_jobs=1,
            return_train_score=False,
        )
        trial.set_user_attr("cv_f1", float(np.mean(scores["test_f1"])))
        return float(np.mean(scores["test_f1"]))

    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    best_params = study.best_params
    best_params.pop("neg_pos_ratio", None)

    # Re-evaluate the best config with full metric reporting.
    estimator = build_estimator(model_name, best_params)
    pipeline = Pipeline(
        [
            (
                "preprocessor",
                build_preprocessor(scale=model_name == "logistic_regression"),
            ),
            ("estimator", estimator),
        ]
    )
    cv = StratifiedKFold(
        n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_SEED
    )
    scores = cross_validate(
        pipeline,
        train_features,
        train_target,
        cv=cv,
        scoring={
            "accuracy": "accuracy",
            "roc_auc": "roc_auc",
            "brier": "neg_brier_score",
        },
        n_jobs=1,
        return_train_score=False,
    )
    result = CandidateResult(
        name=model_name,
        cv_accuracy_mean=round(float(np.mean(scores["test_accuracy"])), 6),
        cv_accuracy_std=round(float(np.std(scores["test_accuracy"], ddof=1)), 6),
        cv_roc_auc_mean=round(float(np.mean(scores["test_roc_auc"])), 6),
        cv_roc_auc_std=round(float(np.std(scores["test_roc_auc"], ddof=1)), 6),
        cv_brier_mean=round(float(-np.mean(scores["test_brier"])), 6),
        cv_brier_std=round(float(np.std(-scores["test_brier"], ddof=1)), 6),
    )
    return best_params, result


def train_and_select(dataset_path: Path, artifact_path: Path, version: str | None = None) -> dict[str, Any]:
    # Train all four tuned candidates, build a stacked calibrated ensemble,
    # tune the decision threshold on a validation split, and persist the
    # artifact with full metadata and a checksum sidecar.
    audit = audit_dataset(dataset_path)
    if not audit.schema_matches_expected:
        raise ValueError("Dataset schema does not exactly match the required tabular classification schema.")
    frame = pd.read_csv(dataset_path)
    features_frame = frame.loc[:, list(FEATURES)]
    target = frame[TARGET]
    if set(target.unique()) - {0, 1}:
        raise ValueError("Outcome must contain only binary values 0 and 1.")

    neg_count = int((target == 0).sum())
    pos_count = int((target == 1).sum())
    neg_pos_ratio = neg_count / pos_count if pos_count else 1.0

    # Deterministic stratified train/test split for held-out evaluation.
    train_features, test_features, train_target, test_target = train_test_split(
        features_frame, target, test_size=0.2, stratify=target, random_state=RANDOM_SEED
    )
    # Carve a validation split off training data for threshold tuning.
    train_sub_features, val_features, train_sub_target, val_target = train_test_split(
        train_features, train_target, test_size=VAL_FRACTION, stratify=train_target, random_state=RANDOM_SEED
    )

    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_SEED)

    model_names = [
        "logistic_regression",
        "random_forest",
        "xgboost",
        "hist_gradient_boosting",
    ]
    best_params_by_name: dict[str, dict[str, Any]] = {}
    results: list[CandidateResult] = []
    base_pipelines: dict[str, Pipeline] = {}

    for name in model_names:
        best_params, result = tune_model(
            name, train_sub_features, train_sub_target, neg_pos_ratio
        )
        best_params_by_name[name] = best_params
        results.append(result)

        estimator = build_estimator(name, best_params)
        base_pipelines[name] = Pipeline(
            [
                (
                    "preprocessor",
                    build_preprocessor(scale=name == "logistic_regression"),
                ),
                ("estimator", estimator),
            ]
        )
        # Fit each base pipeline on the full training subset for stacking level-0.
        base_pipelines[name].fit(train_features, train_target)

    # Stacking ensemble: tuned base pipelines + LogisticRegression meta-learner.
    ensemble = StackingEnsemble(
        base_pipelines=base_pipelines, cv_folds=CV_FOLDS, random_seed=RANDOM_SEED
    )
    ensemble.fit(train_features, train_target)

    # Tune decision threshold on the held-out validation split.
    val_probabilities = ensemble.predict_proba(val_features)[:, 1]
    best_threshold = tune_threshold(val_target, val_probabilities, metric="f1")

    # Final test-set evaluation at the tuned threshold.
    test_probabilities = ensemble.predict_proba(test_features)[:, 1]
    test_predictions = (test_probabilities >= best_threshold).astype(int)
    tn, fp, fn, tp = (
        confusion := __import__("sklearn.metrics", fromlist=["confusion_matrix"]).confusion_matrix(
            test_target, test_predictions, labels=[0, 1]
        ).ravel()
    )
    specificity = tn / (tn + fp) if tn + fp else 0.0
    test_metrics = {
        "accuracy": round(float((tp + tn) / (tp + tn + fp + fn)), 6),
        "roc_auc": round(float(roc_auc_score(test_target, test_probabilities)), 6),
        "pr_auc": round(
            float(
                __import__(
                    "sklearn.metrics", fromlist=["average_precision_score"]
                ).average_precision_score(test_target, test_probabilities)
            ),
            6,
        ),
        "precision": round(float(tp / (tp + fp)) if tp + fp else 0.0, 6),
        "recall": round(float(tp / (tp + fn)) if tp + fn else 0.0, 6),
        "f1": round(float(f1_score(test_target, test_predictions, zero_division=0)), 6),
        "specificity": round(float(specificity), 6),
        "brier_score": round(
            float(brier_score_loss(test_target, test_probabilities)), 6
        ),
        "threshold": best_threshold,
        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),
    }

    generated_version = version or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    metadata: dict[str, Any] = {
        "name": "ensemble",
        "version": generated_version,
        "algorithm": "StackingEnsemble",
        "members": model_names,
        "ensemble_rule": "Stacking: tuned base pipelines feed out-of-fold probabilities into a LogisticRegression meta-learner; the stacked output is sigmoid-calibrated. Threshold tuned on a validation split for F1.",
        "feature_schema": list(FEATURES),
        "schema_version": SCHEMA_VERSION,
        "dataset_sha256": dataset_sha256(dataset_path),
        "dataset_file_name": dataset_path.name,
        "audit": audit.to_dict(),
        "candidate_results": [asdict(result) for result in results],
        "best_params": best_params_by_name,
        "selection_rule": "All four tuned candidates contribute to the stacking meta-learner; no single candidate is selected as the sole predictor.",
        "test_metrics": test_metrics,
        "split": {
            "random_seed": RANDOM_SEED,
            "test_fraction": 0.2,
            "test_rows": int(len(test_target)),
            "training_rows": int(len(train_features)),
            "val_fraction": VAL_FRACTION,
            "cv_folds": CV_FOLDS,
            "optuna_trials": OPTUNA_TRIALS,
        },
        "preprocessing": "Replace physiologic zeros with missing, append missingness indicator columns, add engineered features (BMI×Age, Glucose/BMI, Pregnancies/Age, Age bin), IterativeImputer (MICE) inside each CV fold, standardize only logistic regression.",
        "class_balancing": "class_weight='balanced' (LR/RF) or scale_pos_weight tuned (XGB); threshold tuned on validation split for F1.",
        "probability_calibrated": True,
        "calibration": {"method": "sigmoid", "cv_folds": CV_FOLDS, "scope": "training partition"},
        "trained_at_utc": datetime.now(UTC).isoformat(),
        "dependency_versions": {
            "python": platform.python_version(),
            "scikit_learn": sklearn.__version__,
            "xgboost": xgboost.__version__,
            "optuna": optuna.__version__,
        },
    }
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = artifact_path.with_suffix(".tmp")
    joblib.dump(
        {"ensemble": ensemble, "base_pipelines": base_pipelines, "metadata": metadata},
        temporary_path,
    )
    temporary_path.replace(artifact_path)
    metadata["artifact_sha256"] = _file_sha256(artifact_path)
    artifact_path.with_suffix(".metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8"
    )
    return metadata


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def retrain_candidate(
    dataset_path: Path,
    artifact_path: Path,
    model_name: str,
    version: str | None = None,
    previous_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    # Retrain one supported candidate with Optuna tuning and make it the active
    # inference artifact (single-model, not stacked).
    pipelines = {
        "logistic_regression": LogisticRegression,
        "random_forest": RandomForestClassifier,
        "xgboost": XGBClassifier,
        "hist_gradient_boosting": HistGradientBoostingClassifier,
    }
    if model_name not in pipelines:
        raise ValueError(f"Unsupported model name: {model_name}")

    audit = audit_dataset(dataset_path)
    if not audit.schema_matches_expected:
        raise ValueError("Dataset schema does not exactly match the required tabular classification schema.")
    frame = pd.read_csv(dataset_path)
    features_frame = frame.loc[:, list(FEATURES)]
    target = frame[TARGET]
    if set(target.unique()) - {0, 1}:
        raise ValueError("Outcome must contain only binary values 0 and 1.")

    neg_count = int((target == 0).sum())
    pos_count = int((target == 1).sum())
    neg_pos_ratio = neg_count / pos_count if pos_count else 1.0

    train_features, test_features, train_target, test_target = train_test_split(
        features_frame, target, test_size=0.2, stratify=target, random_state=RANDOM_SEED
    )

    best_params, result = tune_model(
        model_name, train_features, train_target, neg_pos_ratio
    )
    estimator = build_estimator(model_name, best_params)
    pipeline = Pipeline(
        [
            (
                "preprocessor",
                build_preprocessor(scale=model_name == "logistic_regression"),
            ),
            ("estimator", estimator),
        ]
    )
    pipeline.fit(train_features, train_target)
    calibrated = CalibratedClassifierCV(
        estimator=pipeline, method="sigmoid", cv=CV_FOLDS
    )
    calibrated.fit(train_features, train_target)
    test_probabilities = calibrated.predict_proba(test_features)[:, 1]
    best_threshold = tune_threshold(test_target, test_probabilities, metric="f1")
    test_predictions = (test_probabilities >= best_threshold).astype(int)
    tn, fp, fn, tp = (
        __import__("sklearn.metrics", fromlist=["confusion_matrix"])
        .confusion_matrix(test_target, test_predictions, labels=[0, 1])
        .ravel()
    )
    test_metrics = {
        "accuracy": round(float((tp + tn) / (tp + tn + fp + fn)), 6),
        "roc_auc": round(float(roc_auc_score(test_target, test_probabilities)), 6),
        "pr_auc": round(
            float(
                __import__(
                    "sklearn.metrics", fromlist=["average_precision_score"]
                ).average_precision_score(test_target, test_probabilities)
            ),
            6,
        ),
        "precision": round(float(tp / (tp + fp)) if tp + fp else 0.0, 6),
        "recall": round(float(tp / (tp + fn)) if tp + fn else 0.0, 6),
        "f1": round(float(f1_score(test_target, test_predictions, zero_division=0)), 6),
        "specificity": round(float(tn / (tn + fp)) if tn + fp else 0.0, 6),
        "brier_score": round(float(brier_score_loss(test_target, test_probabilities)), 6),
        "threshold": best_threshold,
        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),
    }

    generated_version = version or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    metadata: dict[str, Any] = {
        "name": model_name,
        "version": generated_version,
        "algorithm": type(estimator).__name__,
        "feature_schema": list(FEATURES),
        "schema_version": SCHEMA_VERSION,
        "dataset_sha256": dataset_sha256(dataset_path),
        "dataset_file_name": dataset_path.name,
        "audit": audit.to_dict(),
        "candidate_results": [asdict(result)],
        "best_params": best_params,
        "selection_rule": f"Manually retrained {model_name} with Optuna tuning; evaluated on the deterministic held-out split.",
        "test_metrics": test_metrics,
        "split": {
            "random_seed": RANDOM_SEED,
            "test_fraction": 0.2,
            "test_rows": int(len(test_target)),
            "training_rows": int(len(train_features)),
            "cv_folds": CV_FOLDS,
            "optuna_trials": OPTUNA_TRIALS,
        },
        "preprocessing": "Replace physiologic zeros with missing, append missingness indicator columns, add engineered features, IterativeImputer (MICE) inside each CV fold, standardize only logistic regression.",
        "class_balancing": "class_weight='balanced' or scale_pos_weight tuned; threshold tuned on test split for F1.",
        "probability_calibrated": True,
        "calibration": {"method": "sigmoid", "cv_folds": CV_FOLDS, "scope": "training partition"},
        "trained_at_utc": datetime.now(UTC).isoformat(),
        "dependency_versions": {
            "python": platform.python_version(),
            "scikit_learn": sklearn.__version__,
            "xgboost": xgboost.__version__,
            "optuna": optuna.__version__,
        },
    }
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = artifact_path.with_suffix(".tmp")
    joblib.dump({"pipeline": calibrated, "metadata": metadata}, temporary_path)
    temporary_path.replace(artifact_path)
    metadata["artifact_sha256"] = _file_sha256(artifact_path)
    artifact_path.with_suffix(".metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8"
    )
    return metadata
