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
    artifact_path = tmp_path / "test-model.joblib"
    training_features = pd.DataFrame(
        [
            [0, 85, 66, 29, 0, 26.6, 0.351, 31],
            [6, 148, 72, 35, 0, 33.6, 0.627, 50],
            [1, 89, 66, 23, 94, 28.1, 0.167, 21],
            [8, 183, 64, 0, 0, 23.3, 0.672, 32],
        ],
        columns=list(FEATURES),
    )
    pipeline = Pipeline([("preprocessor", build_preprocessor(scale=True)), ("estimator", LogisticRegression(max_iter=1000, random_state=2026))])
    pipeline.fit(training_features, [0, 1, 0, 1])
    joblib.dump({"pipeline": pipeline, "metadata": {"name": "test-logistic", "version": "test-v1", "feature_schema": list(FEATURES), "schema_version": SCHEMA_VERSION, "probability_calibrated": False}}, artifact_path)
    settings = Settings(app_env="test", database_url=f"sqlite:///{(tmp_path / 'test.db').as_posix()}", model_artifact_path=artifact_path, cors_origins=["http://localhost:5173"])
    app = create_app(settings)
    with TestClient(app) as test_client:
        Base.metadata.create_all(test_client.app.state.database.engine)
        yield test_client
