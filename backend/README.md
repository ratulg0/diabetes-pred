# GlucoCare backend

FastAPI backend for a **tabular diabetes-classification research prototype**. It is not a medical device, diagnosis service, CGM integration, or glucose-forecasting system.

## What is implemented

- Versioned FastAPI REST endpoints under `/api/v1` with validation, CORS, request IDs and safe error responses.
- Aggregated dataset audit for the repository's `diabetes.csv`; source data is not changed.
- Leakage-safe benchmark pipelines for Logistic Regression, Random Forest, XGBoost and HistGradientBoosting.
- Offline model selection using 5-fold stratified CV on the training split, then a single held-out test evaluation.
- Versioned joblib package containing preprocessing plus estimator, accompanied by a JSON metadata/checksum sidecar.
- SQLAlchemy models and an Alembic initial migration designed for SQL Server; SQLite is supported only for isolated local tests.
- Transactional assessment/result persistence, history, dashboard, model-status and local-demo preferences endpoints.

## Dataset boundary

The inspected file has 768 rows and the exact columns:

`Pregnancies, Glucose, BloodPressure, SkinThickness, Insulin, BMI, DiabetesPedigreeFunction, Age, Outcome`

Its SHA-256 is `698c203a14aa31941d2251175330c9199f3ccdb31597abbba2a3e35416257a72`. The file has the common Pima-style layout, but no provenance is stored in this repository. The benchmark treats zero in five physiologic fields as candidate missing values within the pipeline only; that is a documented modeling assumption, not a fact about an individual record.

## Setup

Requires Python 3.13+.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Without `DATABASE_URL`, the development server automatically creates `backend/.local/glucocare.db` (ignored by Git) so the complete local frontend-to-backend flow works. Set `DATABASE_URL` to a SQL Server URL before deployment or when testing SQL Server migrations. For example:

```dotenv
DATABASE_URL=mssql+pyodbc://user:password@host/database?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no
```

Install SQL Server support separately:

```powershell
pip install -r requirements-sqlserver.txt
```

On the currently tested Python 3.15 Windows environment, `pyodbc==5.3.0` has no matching wheel and requires Microsoft C++ Build Tools to compile. SQL Server connectivity could therefore not be run in this repository; no connection claim is made.

Run migrations and start the API after configuring a database:

```powershell
alembic upgrade head
python -m uvicorn app.main:app --reload
```

For VS Code, use **Debug frontend in Edge** or **Debug frontend in Chrome**. The configured launch task starts the API on `127.0.0.1:8000`, waits for its health endpoint, then starts Vite on `127.0.0.1:5173` before the browser opens.

The process liveness endpoint is `GET /api/v1/health`. Readiness is deliberately `503` until both the database and a trusted model artifact are available.

## Train a model

Training is a controlled offline operation, never an HTTP request:

```powershell
python -m training.compare_models
```

This writes ignored artifacts under `../models/`. It evaluates all four candidates, selects the candidate with the best training-CV ROC-AUC (ties use lower Brier score), then evaluates the selected candidate once on the held-out test data. The metadata JSON records results; do not present those results as clinical validation.

## API

| Method | Route | Notes |
|---|---|---|
| GET | `/api/v1/health` | Process liveness |
| GET | `/api/v1/ready` | Database and artifact readiness |
| POST | `/api/v1/assessments/predict` | Saved-artifact prediction only; no persistence |
| POST | `/api/v1/assessments` | Prediction plus one transaction for assessment/result |
| GET | `/api/v1/assessments` | Paginated records, optional `predicted_class` filter |
| GET/DELETE | `/api/v1/assessments/{id}` | Delete defaults to disabled |
| GET | `/api/v1/dashboard/summary` | Database-backed counts and five recent records |
| GET | `/api/v1/models` | Artifact availability and metadata |
| GET/PUT | `/api/v1/preferences` | Local-development display preferences only |

The API does not return a probability because the baseline pipelines do not add a calibrated-probability step. Every prediction includes the research-prototype disclaimer.

## Tests

```powershell
pytest
```

Tests use a temporary SQLite database and a small local test model. They do not demonstrate SQL Server connectivity or clinical validity.

## Security boundary

Authentication/authorization are not implemented. Do not expose this backend to real users or store real health data. The local preferences scope exists only for development; a future authenticated system must derive ownership server-side rather than trust a browser-supplied user identifier.
