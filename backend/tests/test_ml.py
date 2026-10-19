from __future__ import annotations

from pathlib import Path

from app.ml.data_audit import audit_dataset
from app.ml.schema import EXPECTED_COLUMNS, ZERO_AS_MISSING_FEATURES
from app.ml.train import candidate_pipelines


def test_dataset_audit_confirms_actual_schema() -> None:
    dataset_path = Path(__file__).resolve().parents[2] / "diabetes.csv"
    audit = audit_dataset(dataset_path)
    assert audit.schema_matches_expected
    assert audit.columns == list(EXPECTED_COLUMNS)
    assert audit.row_count == 768
    assert audit.target_distribution == {"0": 500, "1": 268}
    assert all(audit.zero_counts_for_candidate_missing_values[feature] > 0 for feature in ZERO_AS_MISSING_FEATURES)


def test_all_four_benchmark_pipelines_exist() -> None:
    assert set(candidate_pipelines()) == {"logistic_regression", "random_forest", "xgboost", "hist_gradient_boosting"}
