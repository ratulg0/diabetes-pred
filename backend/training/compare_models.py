from __future__ import annotations

import json

from app.core.config import get_settings
from app.ml.train import train_and_select


if __name__ == "__main__":
    settings = get_settings()
    metadata = train_and_select(settings.dataset_path, settings.resolved_model_artifact_path, settings.model_version)
    print(json.dumps(metadata, indent=2, sort_keys=True))
