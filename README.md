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

The legacy root-level Pima `diabetes.csv` has been removed. The replacement CSV is not yet tracked in the repository; copy the supplied file to the path above before training or predictions can work. The application deliberately does not substitute a different-schema dataset.

## Train

From `backend/`, install dependencies and train the active model:

```powershell
pip install -r requirements.txt
python -m training.train_clinical_model
```

Training audits the schema, cross-validates Logistic Regression, Random Forest, XGBoost, and HistGradientBoosting, then fits an equal-weight soft-voting ensemble and writes it to `models/active-model.joblib`. The final class is based on the average of the four predicted probabilities (threshold 0.5). In development, the API also attempts training at startup. The model status endpoint is `GET /api/v1/models`; the retraining endpoint is `POST /api/v1/models/retrain-all`.

## Assessment flow

The existing Clinical Assessment page now submits the 14 fields to `POST /api/v1/assessments`. The API validates the dataset's category values, accepts missing numeric measurements, and permits missing alcohol intake because that field is missing in a large portion of the source data. Preprocessing is fitted within training folds: numeric median imputation and missingness indicators, categorical most-frequent imputation and one-hot encoding.

The parallel uploaded-dataset assessment page has been removed. The separate CDC lifestyle questionnaire remains a distinct feature and is not used by the primary clinical model.

## Safety and limitations

This is an educational/research prototype, **not a clinically validated medical device**. Dataset labels and model scores are not diagnoses, should not guide treatment, and do not replace laboratory testing or a qualified clinician. The dataset's provenance and validity, performance on independent populations, calibration, and fairness require independent review before any clinical use.
