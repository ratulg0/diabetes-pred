# GlucoCare Frontend–Backend Integration Specification

> **Status:** This document specifies how to integrate the current frontend with the planned backend. It does not claim the API or database integration already exists.
>
> Repository: `ratulg0/diabetes-pred`  
> Working branch: `feature/ui-project-structure`  
> Frontend: React 18, TypeScript, Vite, Tailwind CSS v3, React Router, Recharts and Lucide React.  
> Target backend: FastAPI + Pydantic + SQL Server + Python ML pipeline.  
> Current state: the UI uses hardcoded sample records, illustrative charts and demo assessment logic.

## 1. Objective

Connect GlucoCare's existing Overview, New Assessment, Assessment History and Preferences screens to a versioned REST API while preserving the current light theme, blue typography, responsive layout and visual style.

The first release covers tabular classification and saved assessments. CGM ingestion/forecasting is a separate later capability: the current `diabetes.csv` is a tabular classification dataset, not timestamped glucose readings.

## 2. Current frontend facts and integration work

The primary UI is currently implemented in `frontend/src/App.tsx`; `main.tsx`, `index.css` and the Vite/Tailwind configuration support it. The UI currently includes:
- Sample assessment records in local constants.
- Hardcoded dashboard totals.
- Illustrative weekly glucose chart data.
- Illustrative feature-importance bars.
- A demo calculation in the assessment flow rather than a trained model API.
- A demo researcher/profile presentation rather than real authentication.

Replace mock data with API responses incrementally. Do not remove the demo caveats until real behavior is implemented and verified.

Specific safeguards:
- Sample records must not be presented as real history.
- A glucose trend must remain labelled illustrative until real CGM data exists.
- Feature importance must not be presented as real unless derived from the active, versioned model using a documented method.
- Dashboard counts and result distributions must come from the backend or be explicitly labelled demo values.
- The form result must come from the server model, not a frontend formula.
- Buttons, filters, preferences and export controls must work or be labelled unavailable.

## 3. Integration architecture

```text
Browser / React UI
       |
       v
Shared frontend API client
       | HTTP + JSON (/api/v1)
       v
FastAPI routes and Pydantic validation
       |
       +--> Assessment/history/dashboard services
       |
       +--> Saved ML pipeline for inference
       |
       v
Repositories --> SQL Server

Separate offline training scripts produce vetted model artifacts.
Normal HTTP requests must not train models.
```

Responsibilities:
- Frontend: display, interaction, UX validation, request states and response rendering.
- Backend: authoritative validation, predictions, persistence, access control and dashboard aggregation.
- Training pipeline: audit/preprocess data, compare models and create versioned artifacts.
- Database: source of truth for saved assessments and results.

## 4. Proposed API contract

Prefix routes with `/api/v1`. These routes are proposed and must be implemented/tested before the frontend relies on them.

| Method | Endpoint | Used by |
|---|---|---|
| `GET` | `/api/v1/health` | Connectivity/liveness |
| `GET` | `/api/v1/ready` | Optional model/database readiness |
| `POST` | `/api/v1/assessments/predict` | Non-persisted preview, only if needed |
| `POST` | `/api/v1/assessments` | Predict and save an assessment |
| `GET` | `/api/v1/assessments` | History with pagination/filters |
| `GET` | `/api/v1/assessments/{id}` | One assessment |
| `DELETE` | `/api/v1/assessments/{id}` | Delete authorized record, if policy permits |
| `GET` | `/api/v1/dashboard/summary` | Dashboard values and recent activity |
| `GET` | `/api/v1/models` | Active model/version and evaluation metadata |
| `GET` | `/api/v1/preferences` | Read supported preferences |
| `PUT` | `/api/v1/preferences` | Persist supported preferences |

Avoid maintaining two submission flows without a product reason. If clicking Submit always creates a history entry, `POST /assessments` should validate, predict and save in one backend use case. If a user needs a preview before saving, use `/assessments/predict` and save only after explicit confirmation.

### Example request

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

This is a proposed JSON shape, not a final validation policy. Determine allowed ranges, missing-value handling and nullability after auditing the actual dataset. Frontend constraints are not automatically medically authoritative.

### Example response

```json
{
  "id": "server-generated-id",
  "created_at": "2026-10-18T12:00:00Z",
  "result": {
    "predicted_class": 0,
    "probability": null,
    "model_name": "selected-model",
    "model_version": "version-id"
  },
  "disclaimer": "Research prototype only; not a diagnosis or medical advice."
}
```

The example is illustrative, not a real API response. Agree on ID format, timestamps, input echoing, probability semantics and error schema between backend and frontend. `probability` should be null unless the model provides a probability and its calibration/limitations are documented.

## 5. Frontend code organization

Suggested structure (adapt to existing files rather than duplicating responsibilities):

```text
frontend/src/
├── api/
│   ├── client.ts
│   ├── assessments.ts
│   ├── dashboard.ts
│   ├── models.ts
│   └── preferences.ts
├── types/
│   ├── assessment.ts
│   ├── dashboard.ts
│   └── preferences.ts
├── hooks/
│   ├── useAssessmentHistory.ts
│   └── useDashboardSummary.ts
├── components/
│   ├── ui/
│   ├── forms/
│   └── charts/
├── layouts/
├── pages/
│   ├── dashboard/
│   ├── prediction/
│   ├── history/
│   └── settings/
├── App.tsx
├── main.tsx
└── index.css
```

Use one convention for HTTP access: a shared `api/` client plus domain request functions/hooks. Do not duplicate the same API logic in both `api/` and `services/`. Define TypeScript types that match Pydantic response schemas; avoid `any`. Keep form input state separate from server result state.

## 6. API client and environment configuration

Create one shared HTTP wrapper that:
- Reads the API base URL from Vite environment configuration.
- Sets JSON headers and serializes request bodies consistently.
- Handles non-2xx responses with a typed error.
- Parses empty responses safely.
- Has a reasonable timeout/abort approach.
- Avoids blind retries for assessment creation.
- Never logs health payloads, credentials or tokens.

Example `frontend/.env.local`:

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

Vite `VITE_*` variables are included in browser-visible assets. Never place secrets, database credentials or private API keys in them. Commit only a safe `.env.example`; ignore local `.env` files if they contain environment-specific values.

Pick one URL convention:
- Base URL `http://localhost:8000`, and request paths include `/api/v1/...`; or
- Base URL `http://localhost:8000/api/v1`, and request paths omit the prefix.

Do not append `/api/v1` twice. Verify the actual Vite and FastAPI ports when running locally.

## 7. Screen-by-screen integration

### 7.1 Overview

On page load:
1. Request `GET /api/v1/dashboard/summary`.
2. Show loading placeholders while waiting.
3. Render returned values only after success.
4. Show a retryable error state if the API fails.
5. Show an empty state when no records exist; do not fabricate totals.

Possible response fields include `total_assessments`, a clearly defined result distribution, `recent_assessments`, and `active_model`/`model_status`. Final response schema must be agreed with the backend.

The existing weekly glucose chart is not derivable from the tabular assessment dataset. Keep it marked illustrative or replace it with an assessment activity chart. Only use real glucose values after CGM ingestion exists.

Do not show fake model status or placeholder feature importance as real. If explanations are added later, return versioned metadata and describe the explanation method.

### 7.2 New Assessment

Flow:
1. User enters the eight expected fields.
2. Frontend performs basic UX validation and numeric parsing.
3. Backend performs authoritative schema/range validation.
4. Submit to `POST /api/v1/assessments` to save and predict, or use the separate preview flow if required.
5. Disable duplicate submission and show a pending state.
6. Render the actual server result with its disclaimer.
7. Refresh/invalidate history and dashboard data.
8. Map validation errors to fields where possible.
9. Show a safe error message if network, model or database fails.

The frontend must not calculate the predicted class or probability. Use neutral wording such as “Model output” and never call it a diagnosis. Avoid a second save call if the initial POST already creates the assessment.

### 7.3 Assessment History

Use `GET /api/v1/assessments` with server-side pagination, search and filters when possible. Proposed query parameters: `page`, `page_size`, `search`, a documented result filter, `sort_by` and `sort_order`. Implement only parameters supported by the API; cap `page_size` on the server.

A paginated response should contain `items`, `page`, `page_size` and `total_count`. Show loading, no-results and error states. Changing a filter should fetch the matching server page; do not filter only the currently visible page while claiming to search all records.

#### CSV export

If export promises all matching records, implement a backend export endpoint or fetch all authorized pages carefully. Do not export only the visible page while labelling it “Export all.” Escape CSV values and guard against spreadsheet formula injection (e.g. values beginning with `=`, `+`, `-` or `@`). Export only fields appropriate for the current user.

### 7.4 Preferences

Only persist settings that have a defined effect. Cosmetic-only settings can remain local if that's acceptable. For cross-session/device persistence, use `GET/PUT /api/v1/preferences` and associate preferences with an authenticated user.

Changing glucose units must convert values correctly, not merely change the label. Do not add CGM-specific settings before CGM readings exist.

### 7.5 Model metadata

A future model information panel may show active model name/version, training time, dataset version and published evaluation metrics. Only display information returned by the backend for the actual artifact. Do not invent accuracy figures or imply clinical validity.

## 8. Request state and user experience

Every request-driven screen should handle:
- `idle`
- `loading`
- `success`
- `empty` where applicable
- `error`

Rules:
- Do not flash fake data while waiting for a real response.
- If showing stale data during refresh, label it as previously loaded.
- Provide retry actions for recoverable failures.
- Prevent duplicate submissions.
- Do not blindly retry non-idempotent create requests.
- Cancel or ignore stale requests when users navigate or change filters quickly.
- Do not expose SQL errors, stack traces or internal details.
- Use accessible status/error announcements.
- Never show a success-looking prediction if the model endpoint failed.

## 9. CORS, networking and deployment

Local development often uses Vite `http://localhost:5173` and FastAPI `http://localhost:8000`; verify the actual ports. Configure FastAPI CORS for the exact frontend origin. CORS is not authentication; avoid unrestricted wildcard origins with credentials.

Verify:
- Browser can reach the health endpoint.
- CORS/preflight requests succeed.
- Production frontend points to the deployed API, not `localhost`.
- Allowed origins match the deployed site.
- HTTPS is used in production.
- API paths and prefix are not duplicated.

A reverse proxy can route `/api` to FastAPI later, but it is not required for local development.

## 10. Error contract

Agree on one error shape, for example:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Please check the submitted fields.",
    "field_errors": {
      "glucose": "Value is outside the accepted range."
    },
    "request_id": "correlation-id"
  }
}
```

This is proposed only. The shared frontend client should map backend errors to typed errors. Distinguish field validation, network failures, unauthorized access (if auth exists), missing records, model-not-ready, database unavailability and unexpected errors. Do not return stack traces to the browser.

## 11. Authentication and data ownership

A local prototype may start in an explicit single-user development mode. Before multi-user use or real health data:
- Implement a real identity mechanism.
- Protect user-owned endpoints.
- Scope history and resource queries on the server.
- Never trust a browser-supplied user ID as proof of ownership.
- Handle expired sessions consistently.
- Keep tokens out of logs and use secure storage/transport practices.

Do not present “Demo Researcher” as a real authenticated account until authentication exists.

## 12. Testing plan

### API client tests
- Correct base URL and route construction.
- JSON request/response behavior.
- Non-2xx responses mapped to typed errors.
- Empty response handling.
- Timeout/abort behavior.
- No secrets or health payloads in logs.

### UI tests
- Dashboard renders backend summary and loading/empty/error states.
- Assessment sends the expected payload.
- Field errors map correctly.
- Result is the server result, not local demo logic.
- Duplicate submit is prevented.
- History search/filter/pagination use API parameters.
- CSV export matches its stated scope.
- Preferences save/reload if persistence is implemented.

### End-to-end checks
1. Start SQL Server and apply migrations.
2. Start FastAPI; check `/health` and `/ready`.
3. Ensure a compatible trained artifact exists for prediction tests.
4. Start Vite with the correct API URL.
5. Submit an assessment and verify a database record/result.
6. Refresh and confirm history persists.
7. Confirm dashboard counts match stored records.
8. Simulate unavailable model/network/database and verify safe error states.
9. Test invalid input, empty history and filtering.
10. Confirm browser assets do not contain database credentials or model artifacts.

Use a disposable test database. Never run tests against production health data.

## 13. CGM integration is separate

Do not connect the current weekly chart to classifier output or manufacture timestamps. A later CGM integration would need a separate contract, for example:
- `POST /api/v1/cgm/readings`
- `GET /api/v1/cgm/readings`
- `POST /api/v1/cgm/forecasts`
- `GET /api/v1/cgm/forecasts`

These require timestamped readings, units, source/device quality metadata, user authorization, time-series storage and a trained/evaluated forecasting model. They are not part of the first integration release.

## 14. Suggested implementation sequence

1. Agree on request/response schemas and `/api/v1` convention.
2. Implement health/readiness and verify browser connectivity.
3. Add shared API client and environment configuration.
4. Audit/preprocess data, train/evaluate four candidates, create a vetted artifact.
5. Connect assessment submission to real inference and persistence.
6. Add history queries and database-backed records.
7. Connect dashboard summary to backend data.
8. Connect only meaningful preferences.
9. Finish loading/error/empty states, accessibility and CSV export.
10. Add integration tests, security configuration and deployment documentation.
11. Implement CGM only when appropriate time-series data and requirements exist.

This avoids building the UI against a changing API contract.

## 15. Acceptance checklist

- [ ] Backend contract and TypeScript types agree.
- [ ] API URL is environment-configurable and contains no secrets.
- [ ] CORS matches the frontend origin.
- [ ] Shared client handles errors consistently.
- [ ] Assessment submits to FastAPI.
- [ ] Result comes from the saved model, not frontend demo logic.
- [ ] Assessment and result are persisted exactly once.
- [ ] History uses SQL Server and documented filters.
- [ ] Dashboard values come from the backend or are labelled demo.
- [ ] Glucose/feature charts are not misrepresented as real.
- [ ] Preferences claim persistence only if implemented.
- [ ] Loading, empty, success and error states work.
- [ ] Multi-user access is protected before real data is used.
- [ ] Tests cover client, forms, history, persistence and failures.
- [ ] Deployment URL, CORS, HTTPS and artifact paths are documented.
- [ ] No unsupported claim of CGM integration or clinical validity.

## 16. Instructions for the coding agent

1. Inspect the current UI and backend files before editing.
2. Do not assume proposed endpoints already exist.
3. Implement and verify one end-to-end feature at a time.
4. Keep HTTP calls out of presentation components.
5. Preserve the current visual design.
6. Do not invent responses, metrics, records or CGM data.
7. Run relevant tests/builds and report actual results.
8. Keep this document aligned with the implemented API contract.
9. Report changed files, implemented endpoints, test results and limitations.

## 17. Implementation notes (2026-10-19)

- The React app now uses a shared typed client in `frontend/src/api/` with `VITE_API_BASE_URL` (default `http://127.0.0.1:8000`), timeouts and typed API errors.
- New Assessment calls `POST /api/v1/assessments`; it no longer calculates a browser-side score. A successful response is displayed as a model class with the server disclaimer and refreshes dashboard state.
- Dashboard, history and preferences now render backend responses with loading, empty and retryable error states. History uses server-side `page`, `page_size`, `search` (assessment ID) and `predicted_class` filters. CSV export is explicitly limited to the displayed page and escapes spreadsheet formula prefixes.
- The backend provides a local ignored SQLite development database when `DATABASE_URL` is absent; a configured SQL Server URL still takes precedence and should use Alembic migrations. This enables local end-to-end development without claiming that SQL Server was tested.
- The VS Code debugger launch task starts both services and waits for API/Vite readiness. The model is still trained offline; startup reports a clear error if the required artifact is absent.
