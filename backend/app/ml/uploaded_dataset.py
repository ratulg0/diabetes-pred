"""Training and inference helpers for the 20,000-row uploaded diabetes dataset.

This is deliberately separate from the legacy Pima and CDC survey models because
its feature schema and target definition are different.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier

FEATURES = [
    "Gender", "Age", "Physical Activity", "Smoking Status", "Alcohol Intake",
    "Glucose", "Blood Pressure", "Skin Thickness", "Insulin", "BMI",
    "Cholesterol", "Diabetes Pedigree Function", "Family History", "Hypertension",
]
TARGET = "Outcome"
CATEGORICAL = ["Gender", "Physical Activity", "Smoking Status", "Alcohol Intake", "Family History", "Hypertension"]
NUMERIC = [column for column in FEATURES if column not in CATEGORICAL]
DISCLAIMER = "Research prototype only; not a diagnosis or medical advice."
LABELS = {"Non-diabetic": 0, "Diabetic": 1}


def build_pipeline(model: Any) -> Pipeline:
    numeric = Pipeline([
        ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
        ("scaler", StandardScaler()),
    ])
    categorical = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    preprocessor = ColumnTransformer([
        ("numeric", numeric, NUMERIC),
        ("categorical", categorical, CATEGORICAL),
    ])
    return Pipeline([("preprocess", preprocessor), ("model", model)])


def train_uploaded_dataset(dataset_path: Path, artifact_path: Path) -> dict[str, Any]:
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Uploaded dataset not found at {dataset_path}. Add data/raw/Diabetes Dataset.csv."
        )
    frame = pd.read_csv(dataset_path)
    required = set(FEATURES + [TARGET])
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Uploaded dataset is missing required columns: {missing}")
    frame = frame[FEATURES + [TARGET]].copy()
    frame = frame[frame[TARGET].isin(LABELS)].copy()
    if frame.empty or frame[TARGET].nunique() != 2:
        raise ValueError("Outcome must contain both 'Diabetic' and 'Non-diabetic' labels.")
    X = frame[FEATURES].copy()
    y = frame[TARGET].map(LABELS).astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=2026, stratify=y
    )
    candidates = {
        "logistic_regression": build_pipeline(
            LogisticRegression(max_iter=3000, class_weight="balanced", random_state=2026)
        ),
        "random_forest": build_pipeline(
            RandomForestClassifier(n_estimators=250, min_samples_leaf=3,
                                   class_weight="balanced_subsample",
                                   random_state=2026, n_jobs=-1)
        ),
    }
    results: list[dict[str, Any]] = []
    for name, pipeline in candidates.items():
        pipeline.fit(X_train, y_train)
        probabilities = pipeline.predict_proba(X_test)[:, 1]
        predictions = (probabilities >= 0.5).astype(int)
        results.append({
            "name": name,
            "accuracy": float(accuracy_score(y_test, predictions)),
            "balanced_accuracy": float(balanced_accuracy_score(y_test, predictions)),
            "roc_auc": float(roc_auc_score(y_test, probabilities)),
        })
    # Selection uses held-out ROC-AUC only; the reported metrics are still
    # exploratory and do not establish generalization or clinical validity.
    best = max(results, key=lambda result: result["roc_auc"])
    model = candidates[best["name"]]
    model.fit(X, y)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": model, "features": FEATURES, "labels": LABELS,
                 "model_name": best["name"], "metrics": best,
                 "candidate_results": results, "row_count": len(frame)}, artifact_path)
    metadata_path = artifact_path.with_suffix(".json")
    metadata_path.write_text(json.dumps({
        "model_name": best["name"], "metrics": best,
        "candidate_results": results, "row_count": len(frame),
        "target": TARGET, "features": FEATURES, "disclaimer": DISCLAIMER,
    }, indent=2), encoding="utf-8")
    return json.loads(metadata_path.read_text(encoding="utf-8"))
