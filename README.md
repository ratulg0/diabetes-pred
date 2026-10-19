# GlucoCare

GlucoCare's **primary clinical assessment** is configured for the supplied 20,000-row dataset, not the legacy Pima dataset. The same model pipeline serves the existing `/assessment` page, `POST /api/v1/assessments`, model status, history, and retraining endpoints.

## Replacement dataset

Place the supplied CSV at:

```text
data/raw/Diabetes Dataset.csv
```

It must contain these 15 columns (14 predictors plus target), with the exact spelling and spaces:

- Predictors: `Gender`, `Age`, `Physical Activity`, `Smoking Status`, `Alcohol Intake`, `Glucose`, `Blood Pressure`, `Skin Thickness`, `Insulin`, `BMI`, `Cholesterol`, `Diabetes Pedigree Function`, `Family History`, `Hypertension`
- Target: `Outcome`, containing `Diabetic` or `Non-diabetic`

The application does not fall back to the old root-level `diabetes.csv`; that file uses a different schema and must not be used for the replacement model. The dataset CSV itself needs to be present at the path above before training or predictions can work.

## Train

From `backend/`, install dependencies and train the active model:

```powershell
pip install -r requirements.txt
python -m training.train_clinical_model
```

Training audits the schema, performs stratified cross-validation to select between Random Forest and Extra Trees, evaluates the selected model on a held-out split, and writes the active artifact to `models/active-model.joblib`. In development, the API also attempts training at startup. The model status endpoint is `GET /api/v1/models`; the retraining endpoint is `POST /api/v1/models/retrain-all`.

## Assessment flow

The existing Clinical Assessment page now submits the 14 fields to `POST /api/v1/assessments`. The API validates the dataset's category values, accepts missing numeric measurements, and permits missing alcohol intake because that field is missing in a large portion of the source data. Preprocessing is fitted within training folds: numeric median imputation and missingness indicators, categorical most-frequent imputation and one-hot encoding.

The parallel uploaded-dataset assessment page has been removed. The separate CDC lifestyle questionnaire remains a distinct feature and is not used by the primary clinical model.

## Safety and limitations

This is an educational/research prototype, **not a clinically validated medical device**. Dataset labels and model scores are not diagnoses, should not guide treatment, and do not replace laboratory testing or a qualified clinician. The dataset's provenance and validity, performance on independent populations, calibration, and fairness require independent review before any clinical use.
