# Uploaded diabetes dataset integration

This integration adds a **separate** model flow for the uploaded 20,000-row CSV while preserving the existing Pima clinical assessment and CDC lifestyle assessment flows.

## Dataset

Copy the supplied CSV to:

`data/raw/Diabetes Dataset.csv`

Required target values are `Diabetic` and `Non-diabetic`. The model uses the 14 feature columns in the dataset. This dataset is distinct from the repository's original Pima-style `diabetes.csv` and from the CDC survey dataset.

## Train the model

From the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m training.train_uploaded_dataset
```

The model and metadata are written under `models/uploaded-dataset-model.joblib` and `models/uploaded-dataset-model.json`. The API can also train it on the first prediction request if the CSV is present and the artifact is missing.

## Start the API and frontend

Run the backend using your existing GlucoCare launch configuration, then in a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `/dataset-assessment` in the frontend. The API endpoint is `POST /api/v1/dataset-assessments/predict`.

## Important

- The model's probability is a statistical output, not a clinical risk score or diagnosis.
- The uploaded dataset's origin, measurement units, label definitions, and possible synthetic patterns must be independently reviewed.
- The very high metrics previously observed on this dataset are a warning to investigate data generation, leakage, and representativeness. Do not interpret them as evidence of clinical validity.
- The dataset file is not included in this source patch. Add the supplied CSV at the path above before training.
