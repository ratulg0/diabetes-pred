# GlucoCare Backend Implementation Specification

> **Status:** This is an implementation specification, not a claim that the backend already exists. Inspect the repository and verify each feature before reporting it as implemented.
>
> Repository: `ratulg0/diabetes-pred`  
> Working branch: `feature/ui-project-structure`  
> Existing frontend: React 18, TypeScript, Vite, Tailwind CSS v3, React Router, Recharts and Lucide React.  
> Current backend status: not yet implemented.

## 1. Objective and scope

Build a maintainable backend for GlucoCare that provides:
- Validated REST APIs.
- Reproducible dataset auditing and preprocessing.
- Training and evaluation of four candidate classifiers.
- Inference through a saved, versioned model pipeline.
- SQL Server persistence for assessments and results.
- Dashboard summary, assessment history and model metadata endpoints.
- Automated tests, configuration, logging and deployment documentation.

The first release is a **tabular diabetes-classification prototype** using the existing `diabetes.csv`. The file appears to follow the common Pima Indians Diabetes schema, but the agent must inspect the actual file and confirm provenance before relying on this assumption. It is not timestamped continuous glucose monitoring (CGM) data. Do not claim it supports CGM forecasting.

Out of scope for the first release: real CGM ingestion/forecasting, medical-device integration, claims of clinical validation, and use with real personal health data before security/privacy controls are reviewed.

## 2. Recommended stack

| Concern | Recommendation | Purpose |
|---|---|---|
| API | FastAPI | REST endpoints and OpenAPI docs |
| Language/runtime | Python, pinned supported version | Backend and ML code |
| Schemas | Pydantic | Request/response validation |
| ML | scikit-learn, XGBoost | Four candidate classifiers |
| Data | pandas, NumPy | Audit and preprocessing |
| Database | SQL Server | Relational persistence |
| Database access | SQLAlchemy + `pyodbc` | Connection management and queries |
| Migrations | Alembic | Versioned schema changes |
| Tests | pytest, FastAPI TestClient/httpx | Unit and integration tests |
| Artifacts | Versioned model files and metadata | Reproducible inference |
| Deployment | Docker-compatible container | Consistent runtime |

Pin dependency versions and verify compatibility. Do not use floating `latest` dependencies for a release. SQL Server driver/authentication setup varies by OS, so document the configuration actually tested.

## 3. Proposed structure

```text
backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── dependencies.py
│   │   └── routes/
│   │       ├── health.py
│   │       ├── assessments.py
│   │       ├── history.py
│   │       ├── dashboard.py
│   │       ├── models.py
│   │       ├── preferences.py
│   │       └── auth.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── security.py
│   ├── db/
│   │   ├── session.py
│   │   └── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   └── ml/
│       ├── data_audit.py
│       ├── data_validation.py
│       ├── preprocessing.py
│       ├── train.py
│       ├── evaluate.py
│       ├── predict.py
│       ├── registry.py
│       └── artifacts/
├── training/
│   └── compare_models.py
├── scripts/
├── tests/
│   ├── api/
│   ├── services/
│   └── ml/
├── requirements.txt
├── alembic.ini
├── Dockerfile
├── .env.example
└── README.md
```

At repository level, keep source data in `data/raw/`, intermediate data in `data/interim/`, reproducibly processed data in `data/processed/`, and generated artifacts in `models/`. Ignore secrets, private datasets, generated exports, and model artifacts unless there is a deliberate artifact-storage policy.

### Layer responsibilities

- **Routes:** HTTP semantics and schema binding. Avoid embedding SQL and ML logic here.
- **Schemas:** typed request, response, pagination and filter models.
- **Services:** application use cases, such as predicting and saving an assessment.
- **Repositories:** database operations.
- **ML module:** data audit, preprocessing, training, evaluation, artifact loading and inference.
- **Core:** configuration, security, logging and error handling.

## 4. Dataset audit and preprocessing (mandatory)

Preprocessing must be designed and tested before model training. Do not overwrite the source CSV.

### Audit first

Produce a report covering:
- File hash/version, row/column counts and actual column names.
- Data types, unexpected columns, duplicates and target distribution.
- Missing values and missingness percentage per feature.
- Numeric ranges, impossible values and outliers.
- Zero counts in physiological fields.
- Whether the dataset matches the expected schema.

Do not publish individual records in the report.

### Validate the schema

The presumed dataset has eight input features and `Outcome` as target. Verify this before implementation. The API must not accept `Outcome` as user input. Define the canonical feature order in one place and test it.

```python
FEATURES = [
    "Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
    "Insulin", "BMI", "DiabetesPedigreeFunction", "Age",
]
TARGET = "Outcome"
```

This is a proposed schema, not proof the current file has been validated.

### Investigate zero values

Some versions of this dataset encode missing measurements as zero in `Glucose`, `BloodPressure`, `SkinThickness`, `Insulin` and `BMI`. Confirm the actual dataset definition before treating zeros as missing.

- `Pregnancies = 0` is valid.
- `Outcome = 0` is a valid target.
- Do not convert every zero in every column to missing.
- Document each transformation and retain the original raw data.

### Leakage-safe preprocessing

A reasonable initial benchmark:
- Impute missing numeric values using statistics learned only from the training fold.
- Scale features for Logistic Regression.
- Scaling is usually unnecessary for tree-based models.
- Evaluate explicit imputation versus native missing-value support where appropriate.
- Preserve feature names/order and types at inference.
- Use `Pipeline`/`ColumnTransformer` so every transformation is fitted inside each training fold.

Never impute or scale the entire dataset before splitting. That leaks information into validation/test results.

### Splitting

- Hold out a stratified test set before model selection where feasible.
- Use stratified cross-validation on training data for comparison.
- Fit preprocessing separately within each fold.
- Use the held-out test set only after model choices are fixed.
- Record random seeds and split strategy.
- Investigate grouped splitting if duplicate observations or relevant grouping exist.

The dataset is small; report fold variation and sample counts. Good scores on this dataset do not establish clinical validity or generalization.

## 5. Four-model benchmark

Train and compare:

1. **Logistic Regression** — interpretable baseline; typically benefits from scaling and regularization.
2. **Random Forest** — nonlinear tree ensemble; tune tree depth, leaf size and class weighting conservatively.
3. **XGBoost** — boosted trees; pin the dependency and control overfitting on the small dataset.
4. **HistGradientBoosting** — scikit-learn gradient boosting; evaluate regularization and missing-value handling.

Evaluate using ROC-AUC and, where useful, PR-AUC, precision, recall, F1, specificity at a documented threshold, confusion matrix, and calibration/Brier score if probabilities will be displayed. Report fold variation and test-set counts. Do not select based on accuracy alone.

Train all four in a common evaluation harness. Select a deployment candidate using a documented rule defined before examining final test performance. Keep the other models' evaluation metadata for comparison. Do not average all predictions unless a separately tested ensemble performs better.

## 6. Model artifact and inference contract

Package the fitted preprocessing and estimator together. Record:
- Model name/version and algorithm.
- Dataset/source version or hash.
- Feature schema/order and preprocessing rules.
- Training code commit and dependency versions.
- Validation/test metrics, threshold/calibration details if applicable.
- Training timestamp and artifact checksum.

Load only trusted artifacts: pickle/joblib loading can execute code. Do not silently replace a working artifact when training fails.

For each prediction:
1. Validate the request schema and numeric values.
2. Verify that the model artifact is available and matches the expected schema.
3. Build a single-row feature frame in canonical order.
4. Apply the saved pipeline.
5. Return predicted class and only a probability if supported and appropriately calibrated.
6. Include model name/version and prototype disclaimer.
7. Persist the assessment/result through the application service when requested.
8. Return a controlled error if the model is unavailable; never fabricate a result.

Training is an offline script or controlled admin task, not part of ordinary request handling.

## 7. Proposed REST API

Prefix routes with `/api/v1`. These are proposed until implemented and tested.

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/api/v1/health` | Process liveness |
| `GET` | `/api/v1/ready` | Dependency/model readiness |
| `POST` | `/api/v1/assessments/predict` | Prediction without saving, if needed |
| `POST` | `/api/v1/assessments` | Predict and persist assessment/result |
| `GET` | `/api/v1/assessments` | Paginated history |
| `GET` | `/api/v1/assessments/{id}` | One authorized record |
| `DELETE` | `/api/v1/assessments/{id}` | Delete authorized record if policy permits |
| `GET` | `/api/v1/dashboard/summary` | Real summary counts/recent records |
| `GET` | `/api/v1/models` | Active model and evaluation metadata |
| `GET` | `/api/v1/preferences` | Read supported preferences |
| `PUT` | `/api/v1/preferences` | Update supported preferences |

Example prediction request:

```json
{
  "pregnancies": 1,
  "glucose": 110,
  "blood_pressure": 72,
  "skin_thickness": 25,
  "insulin": 90,
  "bmi": 28.5,
  "diabetes_pedigree_function": 0.45,
  "age": 32
}
```

This is an illustrative contract. Determine final bounds and null/missing behavior after data audit and domain review. Do not treat frontend field bounds as medically authoritative.

Example response shape:

```json
{
  "prediction_id": "server-generated-id",
  "predicted_class": 0,
  "probability": null,
  "model": {"name": "selected-model", "version": "version-id"},
  "disclaimer": "Research prototype only; not a diagnosis or medical advice."
}
```

Probability is `null` deliberately; populate it only when the chosen pipeline supports it and its limitations/calibration are documented. Agree exact ID and response schemas with the frontend.

Use consistent error bodies and status codes: validation errors, missing resources, unauthorized/forbidden responses when auth exists, dependency-unavailable errors, and generic server errors without stack traces. FastAPI's default `422` may be retained if the frontend maps it consistently.

## 8. SQL Server design

Start with these logical entities:

### `Assessments`
- Primary key and UTC creation timestamp.
- Source/type such as `tabular_assessment`.
- Eight validated feature values or a versioned input representation.
- Schema version and optional processing status.
- User association when authentication is implemented.

### `PredictionResults`
- Primary key and foreign key to assessment.
- Predicted class.
- Nullable probability, if supported.
- Model name/version and UTC timestamp.
- Limited response metadata; avoid unnecessary personal data.

### `ModelVersions`
- Model ID/version, algorithm, artifact path/checksum.
- Dataset version, feature schema and preprocessing version.
- Evaluation metrics, training timestamp and status.
- Controlled active/deployed indicator.

### `UserPreferences`
Only if the application needs preferences to persist across sessions/devices. Include a user key and only supported settings.

### Future `CGMReadings`
Separate future table for timestamp, glucose value/unit, source/device metadata and quality flags. Design retention and indexing after expected volume is understood.

Use foreign keys, constraints, appropriate indexes and Alembic migrations. Use SQLAlchemy parameterized queries. Create assessment and result in one transaction so they cannot become inconsistent.

## 9. Security and operational requirements

Before using real health data:
- Implement authentication and server-side authorization.
- Scope every user's history and resource access on the server.
- Never trust a browser-supplied user ID as proof of ownership.
- Keep secrets in environment variables or a secret manager.
- Use HTTPS in deployment and restrict CORS to real frontend origins.
- Validate inputs, cap request sizes and consider rate limits.
- Do not log raw health inputs, credentials or tokens.
- Define retention/deletion and backup policies.
- Review applicable privacy/legal requirements.
- Do not send health data to analytics/third parties without explicit approval.

`.env` files containing secrets must be ignored by Git. Commit only safe placeholders in `.env.example`.

Use structured logs with request ID, route, latency, status and model version, but not full health payloads. `/health` checks process liveness; `/ready` should check dependencies required to serve predictions. If the model or database is unavailable, report degraded readiness rather than returning demo predictions.

## 10. Testing

### Data/ML
- Schema and target values are validated.
- Missing/zero-value rules are documented and tested.
- No preprocessing leakage occurs.
- Cross-validation uses a pipeline.
- All four candidates train on a test fixture.
- Inference feature order matches training.
- Artifact metadata matches the expected schema.
- Model-unavailable errors are handled.
- Failed training cannot silently replace the active model.

### API/database
- Health/readiness behavior.
- Valid/invalid request schemas.
- Assessment/result transaction and rollback.
- History pagination/filtering and dashboard count accuracy.
- Model-unavailable and database-unavailable responses.
- Authorization tests when auth is implemented.
- Error bodies do not expose stack traces/secrets.
- Tests use an isolated test database.

## 11. Configuration and local setup

Example `.env.example` keys:

```dotenv
APP_ENV=development
API_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:5173
DATABASE_URL=
MODEL_ARTIFACT_PATH=
MODEL_VERSION=
LOG_LEVEL=INFO
```

Never commit real credentials. SQL Server connection details depend on OS, ODBC driver, authentication and instance setup; document the configuration actually tested.

Typical commands after implementation:

```bash
cd backend
python -m venv .venv
# Activate the virtual environment for your shell/OS.
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Training and test commands after their modules exist:

```bash
python -m training.compare_models
pytest
```

Do not claim these commands work until the files/dependencies exist and the commands have actually run.

## 12. Future CGM forecasting

CGM forecasting is a separate capability. It requires timestamped glucose readings and a future target such as 15, 30 or 60 minutes ahead. The current tabular CSV cannot train this model.

Before implementing CGM:
1. Obtain suitable data with known provenance and permitted use.
2. Define units, timestamp/timezone, sampling and sensor-quality rules.
3. Build a separate time-series cleaning and sequence-window pipeline.
4. Split chronologically and/or by participant to avoid leakage.
5. Compare suitable baselines and forecasting models.
6. Evaluate MAE/RMSE per horizon and across participants, including clinically important errors.
7. Design separate reading/forecast schemas and endpoints.
8. Present forecasts as estimates, never treatment instructions.

## 13. Acceptance checklist

- [ ] Backend package/configuration exists and starts in documented environment.
- [ ] Health and readiness endpoints work.
- [ ] SQL Server connectivity and migrations are tested.
- [ ] Source CSV audited and left unchanged.
- [ ] Preprocessing choices documented and tested.
- [ ] Train/validation/test split prevents leakage.
- [ ] Four candidates trained and evaluated with recorded results.
- [ ] Model selection follows a documented rule.
- [ ] Artifact includes preprocessing and version metadata.
- [ ] Prediction endpoint uses the saved model and safe error handling.
- [ ] Assessment/result persistence is transactional.
- [ ] History/dashboard endpoints return database-backed data.
- [ ] API contract is documented and tested.
- [ ] Tests pass in the documented environment.
- [ ] Security/privacy reviewed before real health data use.
- [ ] No claim of clinical validity without evidence.

## 14. Instructions for the coding agent

1. Inspect the repository and branch before editing.
2. Treat this as a plan, not proof of existing functionality.
3. Implement in small, verifiable increments.
4. Inspect the actual CSV before finalizing zero/missing-value rules.
5. Preserve the current frontend and source dataset unless change is required.
6. Keep secrets/private data out of Git.
7. Run available tests and report actual results.
8. Do not invent metrics, artifacts, endpoints, tables or clinical validation.
9. Update this specification if implementation choices change.
10. Summarize files changed, commands run, test results and remaining risks.

## 15. Implementation notes (2026-10-19)

- The backend was implemented in `backend/` with FastAPI, SQLAlchemy, Alembic, Pydantic and a four-candidate scikit-learn/XGBoost benchmark.
- `diabetes.csv` was audited without modification. It has 768 rows, the expected nine columns and SHA-256 `698c203a14aa31941d2251175330c9199f3ccdb31597abbba2a3e35416257a72`; its provenance remains unverified.
- SQLAlchemy models and migrations target SQL Server through `mssql+pyodbc`, while SQLite is used only by isolated automated tests. No SQL Server instance or ODBC driver configuration was available to test in this environment.
- On the installed Python 3.15/Windows environment, `pyodbc==5.3.0` has no prebuilt wheel and requires Microsoft C++ Build Tools. It is therefore pinned in `requirements-sqlserver.txt` instead of the core requirements file. This keeps core API/test installation reproducible while making the SQL Server prerequisite explicit.
- The baseline does not expose a probability because no calibration step has been implemented. Responses return `probability: null` rather than presenting raw model scores as calibrated risk.
- Authentication and authorization are intentionally not implemented. The persistence API is for local development only and must not be exposed to real users or real health data until those controls are added.
