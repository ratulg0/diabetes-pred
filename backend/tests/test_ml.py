# ML unit tests: replacement-dataset schema audit and estimator registry coverage.
from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.ml.data_audit import audit_dataset
from app.ml.schema import EXPECTED_COLUMNS
from app.ml.train import candidate_pipelines


def test_dataset_audit_confirms_replacement_schema(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        [
            ["Female", 31, "Moderate", "Never", "Occasional", 85, 66, 29, 90, 26.6, 180, 0.351, "No", "No", "Non-diabetic"],
            ["Male", 50, "Low", "Former", "Regular", 148, 72, 35, 120, 33.6, 250, 0.627, "Yes", "Yes", "Diabetic"],
            ["Female", 21, "High", "Never", None, 89, 66, 23, 94, 28.1, 160, 0.167, "No", "No", "Non-diabetic"],
            ["Male", 32, "Low", "Current", None, 183, 64, 0, 0, 23.3, 220, 0.672, "Yes", "Yes", "Diabetic"],
        ],
        columns=list(EXPECTED_COLUMNS),
    )
    dataset_path = tmp_path / "Diabetes Dataset.csv"
    frame.to_csv(dataset_path, index=False)

    audit = audit_dataset(dataset_path)

    assert audit.schema_matches_expected
    assert audit.columns == list(EXPECTED_COLUMNS)
    assert audit.row_count == 4
    assert audit.target_distribution == {"Non-diabetic": 2, "Diabetic": 2}
    assert audit.missing_counts["Alcohol Intake"] == 2


def test_candidate_pipelines_use_supported_estimators() -> None:
    assert set(candidate_pipelines()) == {"logistic_regression", "random_forest", "xgboost", "hist_gradient_boosting"}
