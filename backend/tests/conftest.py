# Pytest fixtures: builds a TestClient with a temp SQLite DB and a small local
# test model artifact for API tests.
from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from app.core.config import Settings
from app.db.base import Base
from app.main import create_app
from app.ml.preprocessing import build_preprocessor
from app.ml.schema import FEATURES, SCHEMA_VERSION


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    # Build a small test model artifact and a temporary SQLite database, then
    # create the app and yield a TestClient with tables created.
    artifact_path = tmp_path / "test-model.joblib"
    training_features = pd.DataFrame(
        [
            ["Female", 31, "Moderate", "Never", "Occasional", 85, 66, 29, 90, 26.6, 180, 0.351, "No", "No"],
            ["Male", 50, "Low", "Former", "Regular", 148, 72, 35, 120, 33.6, 250, 0.627, "Yes", "Yes"],
            ["Female", 21, "High", "Never", None, 89, 66, 23, 94, 28.1, 160, 0.167, "No", "No"],
            ["Male", 32, "Low", "Current", None, 183, 64, 0, 0, 23.3, 220, 0.672, "Yes", "Yes"],
        ],
        columns=list(FEATURES),
    )
    pipeline = Pipeline([("preprocessor", build_preprocessor(scale_numeric=True)), ("estimator", LogisticRegression(max_iter=1000, random_state=2026))])
    pipeline.fit(training_features, [0, 1, 0, 1])
    joblib.dump({"pipeline": pipeline, "metadata": {"name": "test-logistic", "version": "test-v1", "feature_schema": list(FEATURES), "schema_version": SCHEMA_VERSION, "probability_calibrated": False}}, artifact_path)
    settings = Settings(app_env="test", database_url=f"sqlite:///{(tmp_path / 'test.db').as_posix()}", model_artifact_path=artifact_path, cors_origins=["http://localhost:5173"])
    app = create_app(settings)
    with TestClient(app) as test_client:
        Base.metadata.create_all(test_client.app.state.database.engine)
        yield test_client
