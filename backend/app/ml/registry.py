# Model artifact loading, checksum verification, and inference. The registry
# guards against missing, invalid, or tampered model packages.
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from app.ml.schema import FEATURES, MODEL_FEATURES


class ModelUnavailableError(RuntimeError):
    """Raised when a trusted, schema-compatible model package is not available."""


@dataclass(frozen=True)
class LoadedModel:
    pipeline: Any
    metadata: dict[str, Any]


class ModelRegistry:
    def __init__(self, artifact_path: Path) -> None:
        self.artifact_path = artifact_path
        self._loaded: LoadedModel | None = None

    def reload(self) -> LoadedModel:
        # Discard the cached model and load the latest artifact from disk.
        self._loaded = None
        return self.load()

    def load(self) -> LoadedModel:
        # Load and validate the artifact package, caching the result in memory.
        if self._loaded is not None:
            return self._loaded
        if not self.artifact_path.is_file():
            raise ModelUnavailableError("No trained model artifact is available. Run the controlled training command first.")
        package = joblib.load(self.artifact_path)
        if not isinstance(package, dict) or "metadata" not in package:
            raise ModelUnavailableError("The model artifact has an invalid package format.")
        # Support both the stacked artifact ("ensemble") and legacy single-model
        # artifacts ("pipeline").
        pipeline = package.get("ensemble") or package.get("pipeline")
        if pipeline is None:
            raise ModelUnavailableError("The model artifact has no usable pipeline.")
        metadata = package["metadata"]
        # The API accepts the 8 raw FEATURES; the pipeline engineers the rest.
        if metadata.get("feature_schema") != list(FEATURES):
            raise ModelUnavailableError("The model artifact feature schema does not match this API.")
        sidecar_path = self.artifact_path.with_suffix(".metadata.json")
        expected_checksum = metadata.get("artifact_sha256")
        if sidecar_path.is_file():
            try:
                expected_checksum = json.loads(sidecar_path.read_text(encoding="utf-8")).get("artifact_sha256", expected_checksum)
            except (OSError, json.JSONDecodeError) as error:
                raise ModelUnavailableError("The model metadata sidecar is invalid.") from error
        if expected_checksum and expected_checksum != _file_sha256(self.artifact_path):
            raise ModelUnavailableError("The model artifact checksum does not match its metadata.")
        self._loaded = LoadedModel(pipeline=pipeline, metadata=metadata)
        return self._loaded

    def status(self) -> dict[str, Any]:
        # Report availability and metadata, or the reason the model is unavailable.
        try:
            model = self.load()
            return {"available": True, "metadata": model.metadata}
        except ModelUnavailableError as error:
            return {"available": False, "reason": str(error)}

    def predict_class(self, values: dict[str, float | int]) -> tuple[int, dict[str, Any]]:
        predicted_class, _, metadata = self.predict(values)
        return predicted_class, metadata

    def predict(self, values: dict[str, float | int]) -> tuple[int, float | None, dict[str, Any]]:
        # Run inference: build a feature frame, predict class and calibrated probability.
        loaded = self.load()
        frame = pd.DataFrame([{feature: values[feature] for feature in FEATURES}], columns=list(FEATURES))
        predicted_class = int(loaded.pipeline.predict(frame)[0])
        probability = None
        if loaded.metadata.get("probability_calibrated") and hasattr(loaded.pipeline, "predict_proba"):
            probability = float(loaded.pipeline.predict_proba(frame)[0][1])
        return predicted_class, probability, loaded.metadata


def _file_sha256(path: Path) -> str:
    # Compute the SHA-256 digest of an artifact file in streaming chunks.
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
