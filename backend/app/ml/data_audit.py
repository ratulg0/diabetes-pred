# Aggregate-only dataset diagnostics for the diabetes CSV. Individual records are
# never emitted; only schema, distribution, and range summaries are produced.
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from app.ml.schema import EXPECTED_COLUMNS, FEATURES, TARGET, ZERO_AS_MISSING_FEATURES


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
    # Compute the file's SHA-256 digest in streaming chunks.
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_dataset(path: Path) -> DatasetAudit:
    # Return aggregate-only dataset diagnostics; individual records are never emitted.
    frame = pd.read_csv(path)
    actual_columns = list(frame.columns)
    expected = set(EXPECTED_COLUMNS)
    unexpected_columns = sorted(set(actual_columns) - expected)
    missing_columns = sorted(expected - set(actual_columns))
    numeric_ranges: dict[str, dict[str, float | None]] = {}
    for column in actual_columns:
        if pd.api.types.is_numeric_dtype(frame[column]):
            numeric_ranges[column] = {
                "min": _optional_float(frame[column].min()),
                "max": _optional_float(frame[column].max()),
            }
    target_distribution: dict[str, int] = {}
    if TARGET in frame.columns:
        target_distribution = {str(key): int(value) for key, value in frame[TARGET].value_counts(dropna=False).items()}
    notes = [
        "The file matches the common Pima-style column layout, but provenance is not documented in this repository.",
        "Zeros in Glucose, BloodPressure, SkinThickness, Insulin, and BMI are tracked as candidate missing encodings for a benchmark pipeline; this is an explicit modeling assumption, not proof about an individual record.",
        "This is tabular classification data, not continuous glucose monitoring data.",
    ]
    return DatasetAudit(
        file_name=path.name,
        sha256=dataset_sha256(path),
        row_count=int(len(frame)),
        column_count=int(len(actual_columns)),
        columns=actual_columns,
        dtypes={column: str(dtype) for column, dtype in frame.dtypes.items()},
        schema_matches_expected=actual_columns == list(EXPECTED_COLUMNS),
        unexpected_columns=unexpected_columns,
        missing_columns=missing_columns,
        duplicate_rows=int(frame.duplicated().sum()),
        target_distribution=target_distribution,
        missing_counts={column: int(value) for column, value in frame.isna().sum().items()},
        missing_percentages={column: round(float(value) * 100 / len(frame), 4) for column, value in frame.isna().sum().items()},
        numeric_ranges=numeric_ranges,
        zero_counts_for_candidate_missing_values={column: int((frame[column] == 0).sum()) for column in ZERO_AS_MISSING_FEATURES if column in frame},
        notes=notes,
    )


def _optional_float(value: Any) -> float | None:
    return None if pd.isna(value) else float(value)
