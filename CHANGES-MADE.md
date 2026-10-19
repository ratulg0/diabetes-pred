# Changes Made — GlucoCare Dual Assessment

Date: 2026-10-19
Target branch: `main`

## Implemented

### New Lifestyle & Health Indicators page
- Added `frontend/src/pages/LifestyleAssessment.tsx`.
- Added navigation at `/lifestyle-assessment` and a separate page title.
- Added form inputs for the 21 CDC survey indicators: blood pressure, cholesterol, BMI, smoking, stroke, heart conditions, physical activity, fruit/vegetable consumption, alcohol indicator, healthcare access, self-reported general/mental/physical health, walking difficulty, sex category, age band, education, and income.
- Added required-field checks, range-bound numeric inputs, request/loading/error states, clear form action, and a results panel.
- UI clearly explains that the CDC target's positive class combines prediabetes and diabetes.

### Separate FastAPI endpoint
- Added `backend/app/api/routes/lifestyle_assessments.py`.
- Registered the router in `backend/app/main.py`.
- Added `POST /api/v1/lifestyle-assessments/predict` and `GET /api/v1/lifestyle-assessments/status`.
- Uses a distinct artifact at `models/lifestyle/active-model.joblib`; it does not reuse or overwrite the clinical model artifact.
- Validates the expected 21-feature schema before inference.
- Prediction responses include the target definition and research-only disclaimer.

### Independent lifestyle model training
- Added `backend/app/ml/train_lifestyle.py`.
- Fetches UCI ML Repository dataset ID 891 using `ucimlrepo`.
- Trains a separate soft-voting ensemble containing Logistic Regression, Random Forest, XGBoost, and HistGradientBoosting.
- Saves an independent artifact and metadata including source ID, schema, target semantics, dataset digest, train/test row counts, metrics, library versions, and training time.
- Adds `ucimlrepo==0.0.7` to `backend/requirements.txt`.

## Training and run instructions

From the repository root:

```bash
cd backend
pip install -r requirements.txt
python -m app.ml.train_lifestyle
uvicorn app.main:app --reload
```

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `/lifestyle-assessment` in the frontend.

## Important notes / limitations
- The lifestyle model must be trained before its prediction endpoint will return results. Training downloads UCI dataset 891, so a working network connection is required for that command.
- The existing clinical assessment page, its Pima-style schema, and the root `diabetes.csv` were not changed by this commit. The uploaded `Diabetes Dataset.csv` is not present at the repository root in the current GitHub snapshot, so migrating the clinical model to that file cannot be completed safely from this repository state alone.
- The lifestyle target is survey-defined: class 1 combines prediabetes and diabetes. It is not a confirmed diagnosis.
- Automated frontend builds, backend tests, and real dataset training were not run in this GitHub editing session. Please run them locally after pulling.
- Existing feature branches were not deleted because the available GitHub integration does not expose a branch-delete operation. This change is targeted to `main` as requested.
