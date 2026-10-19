"""Train and activate GlucoCare's primary clinical-assessment model.

Run from the backend directory:
    python -m training.train_clinical_model
"""
from __future__ import annotations

import json

from app.core.config import get_settings
from app.ml.train import train_and_select


def main() -> None:
    settings = get_settings()
    metadata = train_and_select(
        settings.dataset_path,
        settings.resolved_model_artifact_path,
        settings.model_version,
    )
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
