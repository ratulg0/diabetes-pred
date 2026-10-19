"""Train the uploaded-dataset model independently of the legacy Pima model.

Run from the backend directory:
    python -m training.train_uploaded_dataset
"""
from pathlib import Path

from app.ml.uploaded_dataset import train_uploaded_dataset

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    metadata = train_uploaded_dataset(
        ROOT / "data" / "raw" / "Diabetes Dataset.csv",
        ROOT / "models" / "uploaded-dataset-model.joblib",
    )
    print("Training complete")
    print(f"Selected model: {metadata['model_name']}")
    print(f"Rows: {metadata['row_count']}")
    print(f"Holdout metrics: {metadata['metrics']}")
    print("These metrics are exploratory and not evidence of clinical validity.")


if __name__ == "__main__":
    main()
