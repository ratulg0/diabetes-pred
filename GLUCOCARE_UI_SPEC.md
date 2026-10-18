# GlucoCare UI Specification for Coding Agents

> **Purpose:** This document is the source of truth for implementing and improving the frontend UI of the `diabetes-pred` project. Give this file to your VS Code coding agent before asking it to make UI changes.

## 1. Project context

- **Project:** GlucoCare — a diabetes and glucose insights UI prototype.
- **Repository:** `ratulg0/diabetes-pred`
- **Current working branch:** `feature/ui-project-structure`
- **Frontend location:** `frontend/`
- **Stack:** React 18, TypeScript, Vite, Tailwind CSS v3, React Router, Recharts, and Lucide React.
- **Current UI entry points:** `frontend/src/main.tsx`, `frontend/src/App.tsx`, and `frontend/src/index.css`.
- **Current stage:** Frontend-only prototype. There is no production prediction API, trained prediction model, CGM sensor integration, authentication, or durable database persistence connected to the UI.

Do not assume the current dataset is continuous glucose monitoring data. The existing `diabetes.csv` is a small tabular classification dataset, not timestamped CGM readings.

## 2. Product goal

Create a modern, calm, accessible, responsive interface for exploring glucose-related information and entering assessment data. It should feel trustworthy and easy to navigate without presenting prototype outputs as medical diagnoses or real sensor readings.

The UI should be suitable for a future application that may connect to a validated backend and real CGM data, but do not invent those integrations now.

## 3. Visual design system

### Overall direction

- Light theme by default.
- White and very light blue-gray surfaces.
- Blue typography and primary actions.
- Clean, spacious, friendly, professional visual language.
- Soft borders, subtle shadows, and rounded cards.
- Clear visual hierarchy; avoid clutter, excessive gradients, and unnecessary decoration.
- Use consistent spacing, typography, border radii, and component states across all screens.

### Suggested design tokens

Treat these as initial guidance; reuse existing tokens if the codebase already defines equivalent values.

| Token | Suggested value | Use |
|---|---|---|
| Page background | `#F5F8FC` | App canvas |
| Card/surface | `#FFFFFF` | Cards, tables, panels |
| Primary blue | `#2563EB` | Primary buttons, links, active navigation |
| Dark blue text | `#163A70` | Headings and emphasis |
| Body text | `#334155` | Main copy |
| Muted text | `#64748B` | Helper text and metadata |
| Border | `#E2E8F0` | Inputs, dividers, card outlines |
| Soft blue | `#EFF6FF` | Selected states and subtle highlights |
| Success | `#15803D` | Non-diagnostic success states |
| Warning | `#B45309` | Cautions and attention states |
| Error | `#B91C1C` | Validation and errors |

### Typography and layout

- Use a readable sans-serif system font.
- Headings should be concise and clearly separated from supporting text.
- Body text should remain comfortable to read on desktop and mobile.
- Use a centered, responsive content area with consistent horizontal padding.
- Cards should have consistent radius and padding.
- Avoid tiny text for essential information.
- Prefer icons from `lucide-react`; keep icon sizes consistent and pair icons with text when meaning may not be obvious.

## 4. Application shell and navigation

Create a consistent app shell with:

- A left sidebar on desktop.
- A compact/collapsible navigation pattern on mobile.
- GlucoCare branding with a simple health/data-related icon.
- Clear active-navigation styling.
- A top bar with the current page title or breadcrumb, plus space for future profile/notification controls only if needed.
- A main content region that adapts to screen width.
- A visible, unobtrusive prototype/data disclaimer where appropriate.

Navigation destinations:

1. **Overview** — dashboard summary.
2. **New Assessment** — form for entering the current tabular dataset features.
3. **Assessment History** — searchable/filterable list of demo assessments.
4. **Preferences** — basic display and prototype settings.

Navigation must work. Do not render dead links or buttons that look interactive but do nothing.

## 5. Screen requirements

### 5.1 Overview dashboard

Purpose: give users a quick, understandable overview of the prototype.

Include:

- Page heading and one-line description.
- Summary/stat cards with clear labels and units.
- A glucose-style trend chart only when it is explicitly labelled as **illustrative demo data**. Do not imply it is live CGM data.
- A feature/metric chart only when its meaning is explained and its demo status is clear.
- A recent-assessments table with a link/action to view history.
- Helpful empty states when data is absent.
- A visible note that charts and figures are sample data and are not medical advice.

Requirements:
- Keep the dashboard uncluttered.
- Charts must have readable axes, tooltips, legends where useful, and responsive sizing.
- Do not make clinical claims based on sample values.
- Do not fabricate real-time readings, alerts, or patient outcomes.

### 5.2 New Assessment

Purpose: collect the fields expected by the existing `diabetes.csv` tabular dataset.

Fields:

| Field | Key | Input guidance |
|---|---|---|
| Pregnancies | `Pregnancies` | Non-negative integer |
| Glucose | `Glucose` | Numeric value; explain expected unit if known |
| Blood Pressure | `BloodPressure` | Numeric value; clarify expected unit if known |
| Skin Thickness | `SkinThickness` | Numeric value; clarify expected unit if known |
| Insulin | `Insulin` | Numeric value; clarify expected unit if known |
| BMI | `BMI` | Numeric value |
| Diabetes Pedigree Function | `DiabetesPedigreeFunction` | Numeric decimal |
| Age | `Age` | Positive integer |

Behavior:

- Use labels, helper text, and appropriate input types.
- Validate required values and numeric ranges sensibly; show field-level messages.
- Do not silently replace a user's input.
- Include Clear/Reset and Submit/Run Assessment actions.
- Disable submission while invalid or while a request is pending.
- Preserve keyboard usability and logical tab order.
- Provide a clear result state after submission.
- Until a real model API exists, any result must be labelled **Demo only — not a medical result**.
- Do not call an illustrative score a clinically validated risk probability.
- Do not use the current tabular form to pretend to forecast future CGM glucose.

### 5.3 Assessment History

Purpose: let users inspect demo assessment records.

Include:

- Search by an appropriate visible field.
- Filter controls with working behavior.
- A responsive table or card layout for narrow screens.
- Clear status labels that do not imply clinical certainty.
- An empty state when there are no matching records.
- CSV export only if the export actually works and includes the displayed records.
- A clear distinction between seeded sample rows and real persisted data.

Do not claim data is saved to a server or database unless that is implemented.

### 5.4 Preferences

Purpose: expose simple, functional UI preferences.

Potential controls:

- Glucose display unit selection (only if it has a defined and correct effect).
- Display preferences.
- Prototype/data notices.
- Future integration placeholders may be shown as disabled, clearly marked “Not connected” controls, but do not imply integrations exist.

Every enabled control must update the UI or state in a visible, understandable way. Avoid settings that do nothing.

## 6. Component and code organization

Keep components small, typed, reusable, and focused. Avoid putting the entire application in one large component.

Suggested organization:

```text
frontend/
├── public/
└── src/
    ├── assets/
    ├── components/
    │   ├── ui/             # Button, Card, Input, Badge, EmptyState, etc.
    │   ├── forms/          # Assessment form and field groups
    │   └── charts/         # Reusable chart wrappers
    ├── pages/
    │   ├── dashboard/
    │   ├── prediction/
    │   ├── history/
    │   └── settings/
    ├── layouts/            # App shell, sidebar, top bar
    ├── hooks/              # Reusable UI hooks
    ├── services/            # API client boundary; mock services for now
    ├── styles/              # Shared styles/tokens if needed
    ├── App.tsx
    ├── main.tsx
    └── index.css
```

Guidelines:

- Use TypeScript types/interfaces for props and data models.
- Keep page-level code in `pages/` and shared primitives in `components/`.
- Keep mock/demo data separate from presentation components.
- Put future API calls behind a service layer rather than calling `fetch` directly from many components.
- Use React Router for navigable screens.
- Reuse the existing stack and dependencies before adding packages.
- Avoid unnecessary abstractions and avoid duplicating styles.
- Remove unused imports and keep the TypeScript compiler clean.
- Do not rename or delete project data or backend folders as part of a UI-only task.

## 7. Responsive behavior

Support at least these layouts:

- **Mobile:** around 320–767 px.
- **Tablet:** around 768–1023 px.
- **Desktop:** 1024 px and wider.

Check that:

- Navigation can be opened and closed on mobile.
- Forms become single-column on narrow screens.
- Summary cards wrap naturally.
- Tables remain usable through responsive layout or controlled horizontal scrolling.
- Charts resize without overflowing.
- Buttons and inputs have comfortable touch targets.
- No content causes unintended horizontal page scrolling.

## 8. Accessibility and interaction

- Use semantic HTML and correct heading hierarchy.
- Associate every form input with a visible label.
- Do not rely on color alone to communicate status.
- Provide visible keyboard focus styles.
- Ensure interactive controls can be used by keyboard.
- Give icon-only buttons accessible names.
- Use sufficient text/background contrast.
- Announce important form errors and status updates appropriately.
- Respect reduced-motion preferences if animations are added.
- Show loading, success, error, and empty states where applicable.
- Avoid excessive animation and motion.

## 9. Medical safety, data integrity, and privacy

This is a prototype, not a medical device.

- Display a concise disclaimer: **“Prototype for educational use only. Not a diagnosis or substitute for professional medical advice.”**
- Never state that the UI diagnoses diabetes or predicts a user's actual future glucose without a validated, connected model and appropriate evaluation.
- Do not invent CGM readings or imply that sample charts come from a real person or connected device.
- Label mock records and demo calculations visibly.
- Do not collect, log, or transmit personal health information to external services in UI-only work.
- Do not add analytics, trackers, or third-party data collection without explicit authorization.
- Avoid storing sensitive health data in browser storage unless a specific requirement and privacy design have been agreed.
- If a real prediction API is introduced later, clearly show loading/error states and explain the result's limitations.

## 10. Current prototype limitations

Unless the implementation changes and is verified, assume:

- The existing CSV is a tabular dataset, not CGM time-series data.
- Dashboard chart data is illustrative.
- Assessment results are mock/demo outputs.
- History records are seeded sample data.
- Preferences may only exist in in-memory UI state.
- No production API, trained model, sensor stream, authentication, or database persistence is connected.
- A successful UI build has not yet been confirmed.

Do not remove these caveats merely to make the interface look more complete.

## 11. Definition of done for UI tasks

Before marking a UI task complete:

- [ ] The requested screen or interaction is implemented.
- [ ] Navigation and visible controls work as described.
- [ ] Desktop, tablet, and mobile layouts are checked.
- [ ] Loading, empty, error, and success states are handled where relevant.
- [ ] Form labels, validation, keyboard focus, and accessible names are present.
- [ ] Demo data and non-clinical outputs are clearly labelled.
- [ ] No unrelated backend/model/data changes were made.
- [ ] TypeScript has no new errors.
- [ ] `npm run build` succeeds, when the environment allows it.
- [ ] Any test/build limitation is reported honestly.
- [ ] The agent summarizes changed files and provides commands to run or verify the UI.

## 12. Instructions for the VS Code coding agent

When this document is supplied as context:

1. Read this specification and inspect the existing files before editing.
2. Work on the current feature branch unless explicitly told otherwise.
3. Focus on frontend UI only unless explicitly asked to implement backend behavior.
4. Preserve the light theme, blue typography/actions, and calm, uncluttered style.
5. Prefer incremental changes and reusable components over a full rewrite.
6. Do not claim an API, trained ML model, CGM integration, persistence, or clinical validity exists unless the repository proves it.
7. Do not make up data or present demo calculations as real predictions.
8. Run available type checks/builds and report their actual results.
9. List files changed, user-visible behavior changed, and remaining limitations in the final response.

## 13. Useful local commands

Run from the repository root:

```bash
cd frontend
npm install
npm run dev
```

Production build and type check:

```bash
cd frontend
npm run typecheck
npm run build
```

If a script or dependency is missing, inspect `frontend/package.json` and report the issue instead of claiming the command passed.
