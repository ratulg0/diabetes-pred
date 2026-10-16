# Diabetes Prediction

Project scaffold for a diabetes prediction application. This commit establishes folders only; application logic and UI implementation are intentionally not included yet.

## Structure

- `frontend/` — user interface, pages, reusable components, styles, assets, and API services.
- `backend/` — API routes, configuration, request/response schemas, business services, and ML integration.
- `data/raw/` — source datasets (keep sensitive or licensed data out of Git).
- `data/processed/` — reproducibly prepared datasets.
- `models/` — locally generated model artifacts; large artifacts should generally be excluded from Git.
- `tests/` — backend and frontend tests.
- `docs/` — architecture, setup, model evaluation, and user documentation.

## UI direction

- Light background with blue text and blue primary actions.
- Clear navigation and readable typography.
- Responsive dashboard cards, accessible forms, and clear loading/error/empty states.
- Charts should include labels and explanations rather than relying on color alone.

## Important scope note

The current `diabetes.csv` is a static patient-level classification dataset, not a time-stamped continuous glucose monitoring (CGM) dataset. CGM forecasting would need a separate time-series dataset and workflow.

No model, API, or interactive UI has been implemented in this scaffold yet.
