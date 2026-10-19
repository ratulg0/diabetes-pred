from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from app.ml.schema import EXPECTED_COLUMNS, FEATURES, TARGET


@dataclass(frozen=True)
class DatasetAudit:
    file_name: str
    sha256: str
    row_count: int
    column_count: int
    columns: list[str]
    dtypes: dict[str, str]
    schema_matches_expected: bool
    unexpected_columns: list[str]
    missing_columns: list[str]
    duplicate_rows: int
    target_distribution: dict[str, int]
    missing_counts: dict[str, int]
    missing_percentages: dict[str, float]
    numeric_ranges: dict[str, dict[str, float | None]]
    zero_counts_for_candidate_missing_values: dict[str, int]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def dataset_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_dataset(path: Path) -> DatasetAudit:
    frame = pd.read_csv(path)
    actual = list(frame.columns)
    expected = set(EXPECTED_COLUMNS)
    ranges: dict[str, dict[str, float | None]] = {}
    for column in actual:
        if pd.api.types.is_numeric_dtype(frame[column]):
            low, high = frame[column].min(), frame[column].max()
            ranges[column] = {
                "min": None if pd.isna(low) else float(low),
                "max": None if pd.isna(high) else float(high),
            }
    target_counts = {}
    if TARGET in frame:
        target_counts = {str(k): int(v) for k, v in frame[TARGET].value_counts(dropna=False).items()}
    return DatasetAudit(
        file_name=path.name,
        sha256=dataset_sha256(path),
        row_count=len(frame),
        column_count=len(actual),
        columns=actual,
        dtypes={k: str(v) for k, v in frame.dtypes.items()},
        schema_matches_expected=set(actual) == expected and len(actual) == len(EXPECTED_COLUMNS),
        unexpected_columns=sorted(set(actual) - expected),
        missing_columns=sorted(expected - set(actual)),
        duplicate_rows=int(frame.duplicated().sum()),
        target_distribution=target_counts,
        missing_counts={k: int(v) for k, v in frame.isna().sum().items()},
        missing_percentages={k: round(float(v) * 100 / max(len(frame), 1), 4) for k, v in frame.isna().sum().items()},
        numeric_ranges=ranges,
        zero_counts_for_candidate_missing_values={},
        notes=[
            "Target labels are dataset labels, not a clinical diagnosis.",
            "Missing values are imputed inside the model pipeline using training-fold statistics.",
            "The dataset's provenance and clinical validity must be independently verified before any clinical use.",
        ],
    )
