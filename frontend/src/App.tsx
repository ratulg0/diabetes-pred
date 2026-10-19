// Top-level React, router, charting, API, and type imports used across all pages and components.
import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { NavLink, Route, Routes, useLocation } from "react-router-dom";
// Lucide icon library imports used in navigation, badges, settings toggles, and pagination.
import {
  Activity,
  Check,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Download,
  HeartPulse,
  LayoutDashboard,
  Menu,
  Search,
  Settings,
  ShieldCheck,
  X,
} from "lucide-react";
// Recharts components for the illustrative glucose area chart on the dashboard.
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
// API error class, backend service client, shared TypeScript types, and the data-fetching hook.
import { ApiError } from "./api/client";
import { glucocareApi } from "./api/glucocare";
import type {
  AssessmentPage,
  AssessmentRecord,
  DashboardSummary,
  ModelMetadata,
  Preferences,
} from "./api/types";
import { useApiResource } from "./hooks/use-api-resource";
import LifestyleAssessment from "./pages/LifestyleAssessment";

// Illustrative sample data for the dashboard area chart (not live CGM data).
const CHART = [
  { day: "Mon", value: 112 },
  { day: "Tue", value: 126 },
  { day: "Wed", value: 119 },
  { day: "Thu", value: 138 },
  { day: "Fri", value: 131 },
  { day: "Sat", value: 145 },
  { day: "Sun", value: 128 },
];
// Shared UI helpers: input field styling, class-name joiner, date formatter,
// prediction label, percentage formatter, model name map, and glucose unit display.
const fieldClass =
  "mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-50";
const cn = (...items: Array<string | false | undefined>) =>
  items.filter(Boolean).join(" ");
const displayDate = (date: string) =>
  new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(
    new Date(date),
  );
const classLabel = (record: AssessmentRecord) =>
  record.prediction_label ||
  (record.predicted_class === 1
    ? "Likely YES for diabetes (model estimate)"
    : "Likely NO for diabetes (model estimate)");
const percent = (value: number | undefined | null) =>
  typeof value === "number" && Number.isFinite(value)
    ? `${(value * 100).toFixed(1)}%`
    : "Not available";
const MODEL_NAMES: Record<string, string> = {
  logistic_regression: "Logistic Regression",
  random_forest: "Random Forest",
  xgboost: "XGBoost",
  hist_gradient_boosting: "HistGradientBoosting",
  ensemble: "Four-model soft-voting ensemble",
};
const modelName = (name: string) => MODEL_NAMES[name] ?? name;
const displayGlucose = (value: number | null | undefined, unit: Preferences["glucose_unit"]) =>
  typeof value !== "number" || !Number.isFinite(value)
    ? "Not recorded"
    : unit === "mmol/L"
      ? `${(value / 18.0182).toFixed(1)} mmol/L`
      : `${value.toFixed(0)} mg/dL`;

// Notice: reusable alert/empty-state card with optional retry action, used for loading, errors, and empty results.
function Notice({
  title,
  message,
  retry,
}: {
  title: string;
  message: string;
  retry?: () => void;
}) {
  return (
    <div
      role="status"
      className="rounded-2xl border border-blue-100 bg-white p-8 text-center shadow-soft"
    >
      <Activity className="mx-auto text-blue-600" />
      <p className="mt-3 font-bold text-blue-950">{title}</p>
      <p className="mt-1 text-sm text-slate-500">{message}</p>
      {retry && (
        <button
          onClick={retry}
          className="mt-4 rounded-xl bg-blue-600 px-4 py-2 text-sm font-bold text-white"
        >
          Try again
        </button>
      )}
    </div>
  );
}

// Shell: shared layout wrapper with collapsible sidebar navigation, header, main content area, and research-prototype footer.
function Shell({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const title =
    (
      {
        "/": "Overview",
        "/assessment": "Clinical lab assessment",
        "/lifestyle-assessment": "Lifestyle & health assessment",
        "/history": "Assessment history",
        "/settings": "Preferences",
      } as Record<string, string>
    )[location.pathname] ?? "Overview";
  const links = [
    ["/", "Overview", LayoutDashboard],
    ["/assessment", "Clinical assessment", Activity],
    ["/lifestyle-assessment", "Lifestyle assessment", HeartPulse],
    ["/history", "Assessment history", ClipboardList],
    ["/settings", "Preferences", Settings],
  ] as const;
  return (
    <div className="min-h-screen bg-canvas text-ink">
      <button
        aria-label="Open navigation"
        onClick={() => setOpen(true)}
        className="fixed left-4 top-4 z-40 rounded-xl bg-white p-2 shadow lg:hidden"
      >
        <Menu />
      </button>
      {open && (
        <button
          aria-label="Close navigation overlay"
          onClick={() => setOpen(false)}
          className="fixed inset-0 z-40 bg-slate-950/30 lg:hidden"
        />
      )}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-blue-100 bg-white p-5 transition-transform lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex items-center gap-3">
          <div className="rounded-2xl bg-blue-600 p-3 text-white">
            <HeartPulse />
          </div>
          <div>
            <b className="text-blue-950">GlucoCare</b>
            <p className="text-xs text-slate-400">Research prototype</p>
          </div>
          <button
            aria-label="Close navigation"
            onClick={() => setOpen(false)}
            className="ml-auto lg:hidden"
          >
            <X />
          </button>
        </div>
        <nav className="mt-10 space-y-1">
          {links.map(([to, label, Icon]) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold",
                  isActive
                    ? "bg-blue-50 text-blue-700"
                    : "text-slate-500 hover:bg-slate-50",
                )
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto rounded-2xl bg-blue-50 p-4 text-xs leading-5 text-blue-900">
          <ShieldCheck size={18} />
          <p className="mt-2 font-bold">Research use only</p>
          <p>Not a diagnosis or medical advice.</p>
        </div>
      </aside>
      <div className="lg:pl-64">
        <header className="sticky top-0 z-30 h-20 border-b border-blue-100 bg-white/90 px-6 py-5 backdrop-blur">
          <p className="text-xs text-slate-400">
            Workspace / <span className="text-blue-600">{title}</span>
          </p>
          <h1 className="font-bold text-blue-950">{title}</h1>
        </header>
        <main className="px-4 py-6 sm:px-8">
          {children}
          <footer className="mt-10 border-t border-blue-100 py-5 text-xs text-slate-400">
            © 2026 GlucoCare · Research prototype · Not a diagnosis.
          </footer>
        </main>
      </div>
    </div>
  );
}

// Badge: pill showing a record's predicted class as likely YES or NO for diabetes.
function Badge({ record }: { record: AssessmentRecord }) {
  return (
    <span
      className={cn(
        "rounded-full px-2.5 py-1 text-xs font-bold",
        record.predicted_class
          ? "bg-amber-50 text-amber-700"
          : "bg-emerald-50 text-emerald-700",
      )}
    >
      {classLabel(record)}
    </span>
  );
}
// Records: renders a paginated table of saved assessments with date, age, glucose, and prediction output, or an empty notice.
function Records({
  records,
  preferences,
}: {
  records: AssessmentRecord[];
  preferences: Preferences;
}) {
  if (!records.length)
    return (
      <Notice
        title="No saved assessments"
        message="Submit an assessment to create the first server-backed record."
      />
    );
  return (
    <div className="overflow-x-auto rounded-2xl border border-blue-100 bg-white shadow-soft">
      <table className="w-full min-w-[620px] text-left text-sm">
        <thead className="bg-slate-50 text-xs text-slate-500">
          <tr>
            <th className="p-4">Assessment</th>
            <th className="p-4">Date</th>
            <th className="p-4">Age</th>
            <th className="p-4">Glucose</th>
            <th className="p-4">Output</th>
          </tr>
        </thead>
        <tbody>
          {records.map((record) => (
            <tr
              key={record.prediction_id}
              className="border-t border-slate-100"
            >
              <td className="p-4 font-bold text-blue-800">
                {record.prediction_id}
              </td>
              <td className="p-4">{displayDate(record.created_at)}</td>
              <td className="p-4">{record.input.age}</td>
              <td className="p-4">
                {displayGlucose(record.input.glucose, preferences.glucose_unit)}
              </td>
              <td className="p-4">
                <Badge record={record} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Dashboard: overview page with stat cards, model status/ensemble benchmark table, illustrative chart, and recent assessments list.
function Dashboard({
  resource,
  preferences,
}: {
  resource: ReturnType<typeof useApiResource<DashboardSummary>>;
  preferences: Preferences;
}) {
  const model = useApiResource(glucocareApi.getModelStatus, []);
  const [retraining, setRetraining] = useState<string | null>(null);
  const [retrainMessage, setRetrainMessage] = useState("");
  const [retrainError, setRetrainError] = useState(false);

  async function retrainAll() {
    setRetraining("all");
    setRetrainMessage("Training all four models and building the ensemble. This may take a few minutes…");
    setRetrainError(false);
    try {
      const response = await glucocareApi.retrainAllModels();
      await model.refresh();
      setRetrainMessage(
        response.available
          ? `All four models trained. The soft-voting ensemble is now active (${response.metadata?.version ?? "new version"}).`
          : "Retraining finished, but the API did not report a ready model.",
      );
      setRetrainError(!response.available);
    } catch (caught) {
      setRetrainMessage(caught instanceof ApiError ? caught.message : "Model retraining failed. Check the backend logs.");
      setRetrainError(true);
    } finally {
      setRetraining(null);
    }
  }

  if (resource.loading && !resource.data)
    return (
      <Notice
        title="Loading dashboard"
        message="Getting saved assessment activity."
      />
    );
  if (resource.error && !resource.data)
    return (
      <Notice
        title="Dashboard unavailable"
        message={resource.error}
        retry={() => void resource.refresh()}
      />
    );
  const summary = resource.data ?? {
    total_assessments: 0,
    higher_class_assessments: 0,
    recent_assessments: [],
  };
  const percentage = summary.total_assessments
    ? `${((summary.higher_class_assessments * 100) / summary.total_assessments).toFixed(1)}%`
    : "—";
  return (
    <div className="mx-auto max-w-6xl">
      <h2 className="text-2xl font-extrabold text-blue-950">
        Research overview
      </h2>
      <p className="mt-1 text-slate-500">
        Saved assessment activity from the backend.
      </p>
      {resource.error && (
        <div role="alert" className="mt-4 rounded-xl bg-amber-50 p-3 text-sm text-amber-900">
          Previously loaded data is shown. {resource.error}
        </div>
      )}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card label="Saved assessments" value={String(summary.total_assessments)} />
        <Card label="Model class 1 outputs" value={percentage} />
        <Card label="Expected features" value="8" />
        <ModelCard
          available={model.data?.available ?? false}
          metadata={model.data?.metadata ?? null}
        />
      </div>
      <BenchmarkTable
        metadata={model.data?.metadata ?? null}
        available={model.data?.available ?? false}
        retraining={retraining}
        retrainMessage={retrainMessage}
        retrainError={retrainError}
        onRetrainAll={() => void retrainAll()}
      />
      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <div className="rounded-2xl border border-blue-100 bg-white p-5 shadow-soft">
          <h3 className="font-bold text-blue-950">Illustrative glucose visualization</h3>
          <p className="mt-1 text-xs text-slate-400">Sample data only · not a live CGM feed</p>
          <div className="mt-5 h-56">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={CHART}>
                <CartesianGrid stroke="#edf2fa" vertical={false} />
                <XAxis dataKey="day" />
                <YAxis domain={[70, 180]} />
                <Tooltip />
                <Area dataKey="value" stroke="#2563eb" fill="#dbeafe" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="rounded-2xl border border-blue-100 bg-white p-6 shadow-soft">
          <h3 className="font-bold text-blue-950">Server-backed model output</h3>
          <p className="mt-3 text-sm leading-6 text-slate-500">
            New assessments are validated, inferred by the active saved pipeline, and persisted once. Outputs are calibrated model estimates, not diagnoses.
          </p>
          <NavLink to="/assessment" className="mt-5 inline-block rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-bold text-white">
            New assessment
          </NavLink>
        </div>
      </div>
      <div className="mt-6">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="font-bold text-blue-950">Recent assessments</h3>
          <NavLink to="/history" className="text-sm font-bold text-blue-600">View history</NavLink>
        </div>
        <Records records={summary.recent_assessments} preferences={preferences} />
      </div>
    </div>
  );
}
// Card: small stat card showing a label and large value for dashboard metrics.
function Card({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-blue-100 bg-white p-5 shadow-soft">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-extrabold text-blue-950">{value}</p>
    </div>
  );
}
// ModelCard: displays whether the active model artifact is trained and ready, plus its name and version.
function ModelCard({
  available,
  metadata,
}: {
  available: boolean;
  metadata: ModelMetadata | null;
}) {
  const name = metadata?.name ? modelName(metadata.name) : "Unavailable";
  const version = metadata?.version ?? "";
  return (
    <div className="rounded-2xl border border-blue-100 bg-white p-5 shadow-soft">
      <p className="text-sm text-slate-500">Model status</p>
      <p
        className={cn(
          "mt-2 text-lg font-extrabold",
          available ? "text-emerald-700" : "text-amber-700",
        )}
      >
        {available ? "Trained and ready" : "Not ready"}
      </p>
      <p className="mt-2 truncate text-xs text-slate-500">
        {available ? `${name} · ${version}` : "Train a compatible artifact to enable assessments."}
      </p>
    </div>
  );
}

// BenchmarkTable: ensemble section with retrain-all button, per-candidate training status cards, and the soft-voting decision rule explanation.
function BenchmarkTable({
  metadata,
  available,
  retraining,
  retrainMessage,
  retrainError,
  onRetrainAll,
}: {
  metadata: ModelMetadata | null;
  available: boolean;
  retraining: string | null;
  retrainMessage: string;
  retrainError: boolean;
  onRetrainAll: () => void;
}) {
  const supportedModels = [
    "logistic_regression",
    "random_forest",
    "xgboost",
    "hist_gradient_boosting",
  ];
  const candidates = metadata?.candidate_results ?? [];
  return (
    <section className="mt-6 rounded-2xl border border-blue-100 bg-white p-5 shadow-soft">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-bold text-blue-950">Ensemble model</h3>
          <p className="mt-1 max-w-2xl text-sm text-slate-500">
            All four algorithms contribute to one final decision by averaging their estimated positive-class probabilities. There is no single-model selection.
          </p>
        </div>
        <button
          type="button"
          disabled={retraining !== null}
          onClick={onRetrainAll}
          className="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-bold text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          {retraining ? "Training all models…" : "Train all models"}
        </button>
      </div>
      {!available && (
        <p className="mt-4 rounded-xl bg-amber-50 p-3 text-sm text-amber-900">
          The ensemble is not ready yet. Train all models to create it.
        </p>
      )}
      {retrainMessage && (
        <p role={retrainError ? "alert" : "status"} className={cn("mt-4 rounded-xl p-3 text-sm", retrainError ? "bg-rose-50 text-rose-800" : "bg-emerald-50 text-emerald-800")}>
          {retrainMessage}
        </p>
      )}
      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {supportedModels.map((name) => {
          const trained = candidates.some((candidate) => candidate.name === name);
          return (
            <div key={name} className="rounded-xl border border-blue-100 bg-slate-50 p-4">
              <p className="font-semibold text-blue-950">{modelName(name)}</p>
              <p className="mt-2 text-xs text-slate-500">
                {available && trained ? "Ensemble member" : "Awaiting training"}
              </p>
            </div>
          );
        })}
      </div>
      {metadata?.ensemble_rule && (
        <p className="mt-4 text-xs leading-5 text-slate-500">
          Decision rule: average all four model probabilities; values at or above 50% produce a likely YES result, otherwise likely NO. The probability is a model estimate, not a clinical risk assessment.
        </p>
      )}
      <p className="mt-3 text-xs leading-5 text-slate-500">
        Research prototype only. Model outputs must not be used to diagnose or rule out diabetes.
      </p>
    </section>
  );
}

// Assessment: form to create and save a new assessment with field validation, plus the saved server result panel below.
function Assessment({
  onSaved,
  notifications,
}: {
  onSaved: () => void;
  notifications: boolean;
}) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [result, setResult] = useState<AssessmentRecord | null>(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const fields = [
    { key: "gender", label: "Gender", kind: "select", options: ["Female", "Male"] },
    { key: "age", label: "Age (years)", kind: "number", min: 1, max: 120, required: true },
    { key: "physical_activity", label: "Physical activity", kind: "select", options: ["Low", "Moderate", "High"] },
    { key: "smoking_status", label: "Smoking status", kind: "select", options: ["Never", "Former", "Current"] },
    { key: "alcohol_intake", label: "Alcohol intake", kind: "select", options: ["Occasional", "Regular"] },
    { key: "glucose", label: "Glucose", kind: "number", min: 0, max: 600, hint: "Use the same unit as the source dataset." },
    { key: "blood_pressure", label: "Blood pressure", kind: "number", min: 0, max: 300 },
    { key: "skin_thickness", label: "Skin thickness", kind: "number", min: 0, max: 150 },
    { key: "insulin", label: "Insulin", kind: "number", min: 0, max: 3000 },
    { key: "bmi", label: "BMI", kind: "number", min: 0, max: 100 },
    { key: "cholesterol", label: "Cholesterol", kind: "number", min: 0, max: 1000 },
    { key: "diabetes_pedigree_function", label: "Diabetes pedigree function", kind: "number", min: 0, max: 10 },
    { key: "family_history", label: "Family history", kind: "select", options: ["No", "Yes"] },
    { key: "hypertension", label: "Hypertension", kind: "select", options: ["No", "Yes"] },
  ] as const;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setResult(null);
    if (!values.age || !values.gender || !values.physical_activity || !values.smoking_status ||
        !values.family_history || !values.hypertension) {
      setError("Complete the demographic and categorical fields. Numeric measurements may be left blank if unavailable.");
      return;
    }
    const numericKeys = ["age", "glucose", "blood_pressure", "skin_thickness", "insulin", "bmi", "cholesterol", "diabetes_pedigree_function"];
    const payload = Object.fromEntries(fields.map((field) => {
      const raw = values[field.key];
      return [field.key, numericKeys.includes(field.key) ? (raw === undefined || raw === "" ? null : Number(raw)) : (field.key === "alcohol_intake" && !raw ? null : raw)];
    })) as AssessmentInput;
    setSaving(true);
    try {
      const saved = await glucocareApi.createAssessment(payload);
      setResult(saved);
      onSaved();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "The assessment could not run. Check that the backend and trained model are ready.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl">
      <div className="rounded-2xl border border-blue-100 bg-gradient-to-r from-blue-50 to-white p-6 sm:p-8">
        <p className="text-xs font-bold uppercase tracking-wider text-blue-600">Replacement dataset · 14 input features</p>
        <h2 className="mt-2 text-2xl font-extrabold text-blue-950">Clinical assessment research prototype</h2>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
          This form now matches the uploaded 20,000-row dataset, including demographics, lifestyle indicators and laboratory-style measurements. Leave unavailable numeric measurements blank; the trained pipeline imputes missing values.
        </p>
        <p className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm leading-5 text-amber-900">
          Important: this dataset and model have not been clinically validated. Results only reproduce the dataset's Diabetic / Non-diabetic label pattern; they are not a diagnosis and must not guide treatment or replace a clinician.
        </p>
      </div>

      <form onSubmit={submit} className="mt-6 rounded-2xl border border-blue-100 bg-white p-5 shadow-soft sm:p-7">
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {fields.map((field) => (
            <label key={field.key} className="block text-sm font-semibold text-slate-700">
              <span>{field.label}</span>
              {"hint" in field && field.hint && <span className="mt-1 block text-xs font-normal text-slate-400">{field.hint}</span>}
              {field.kind === "select" ? (
                <select required={field.key !== "alcohol_intake"} value={values[field.key] ?? ""} onChange={(e) => setValues((v) => ({ ...v, [field.key]: e.target.value }))}
                  className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5">
                  <option value="" disabled={field.key !== "alcohol_intake"}>{field.key === "alcohol_intake" ? "Not provided (optional)" : "Select an answer"}</option>
                  {field.options.map((option) => <option key={option} value={option}>{option}</option>)}
                </select>
              ) : (
                <input type="number" required={field.key === "age"} min={field.min} max={field.max} step="any"
                  value={values[field.key] ?? ""} onChange={(e) => setValues((v) => ({ ...v, [field.key]: e.target.value }))}
                  placeholder={field.key === "age" ? "Enter age" : "Optional if unavailable"}
                  className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5" />
              )}
            </label>
          ))}
        </div>
        {error && <p role="alert" className="mt-5 rounded-xl bg-rose-50 p-3 text-sm text-rose-800">{error}</p>}
        <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-5">
          <button type="button" disabled={saving} onClick={() => { setValues({}); setResult(null); setError(""); }}
            className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-bold text-slate-600">Clear fields</button>
          <button disabled={saving} className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-bold text-white disabled:opacity-60">
            {saving ? <LoaderCircle size={16} className="animate-spin" /> : <Activity size={16} />}
            {saving ? "Running assessment…" : "Run clinical assessment"}
          </button>
        </div>
      </form>

      {result && (
        <section role="status" className="mt-6 rounded-2xl border border-blue-100 bg-white p-6 shadow-soft">
          <p className="text-xs font-bold uppercase tracking-wider text-blue-600">Saved model output</p>
          <h3 className="mt-2 text-xl font-extrabold text-blue-950">{result.prediction_label}</h3>
          {result.probability !== null && <p className="mt-2 text-sm text-slate-600">Model score for dataset class Diabetic: <strong>{(result.probability * 100).toFixed(1)}%</strong></p>}
          <p className="mt-2 text-xs text-slate-400">Model: {result.model.name} · Version {result.model.version} · {displayDate(result.created_at)}</p>
          <p className="mt-4 rounded-xl bg-amber-50 p-3 text-sm leading-5 text-amber-900"><ShieldCheck size={17} className="mr-2 inline" />{result.disclaimer}</p>
          {notifications && <p className="mt-4 rounded-xl bg-emerald-50 p-3 text-xs text-emerald-800">Assessment saved successfully.</p>}
        </section>
      )}
    </div>
  );
}

// History: paginated assessment history with ID search, model-class filter, CSV export, and previous/next navigation.
function History({ preferences }: { preferences: Preferences }) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<"" | "0" | "1">("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<AssessmentPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setData(
        await glucocareApi.getAssessments({
          page,
          pageSize: 20,
          search: query,
          predictedClass: filter,
        }),
      );
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "History could not be loaded.",
      );
    } finally {
      setLoading(false);
    }
  }, [filter, page, query]);
  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 250);
    return () => window.clearTimeout(timer);
  }, [load]);
  const records = data?.items ?? [];
  const totalPages = Math.max(1, Math.ceil((data?.total_count ?? 0) / 20));
  const exportRows = () => {
    const safe = (value: string | number) =>
      `"${String(value)
        .replace(/^([=+\-@])/, "'$1")
        .replace(/"/g, '""')}"`;
    const csv = [
      ["assessment_id", "created_at", "age", "glucose", "model_class"],
      ...records.map((item) => [
        item.prediction_id,
        item.created_at,
        item.input.age,
        displayGlucose(item.input.glucose, preferences.glucose_unit),
        item.predicted_class,
      ]),
    ]
      .map((row) => row.map(safe).join(","))
      .join("\r\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "glucocare-displayed-assessments.csv";
    link.click();
    URL.revokeObjectURL(url);
  };
  return (
    <div className="mx-auto max-w-6xl">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-extrabold text-blue-950">
            Assessment history
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Server-side ID search and model-class filter.
          </p>
        </div>
        <button
          disabled={!records.length}
          onClick={exportRows}
          className="inline-flex items-center gap-2 rounded-xl border border-blue-100 bg-white px-4 py-2.5 text-sm font-bold text-blue-700 disabled:opacity-50"
        >
          <Download size={16} />
          Export displayed
        </button>
      </div>
      <div className="mt-6 flex gap-3 rounded-2xl border border-blue-100 bg-white p-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 text-slate-400" size={17} />
          <input
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setPage(1);
            }}
            placeholder="Search assessment ID…"
            className="w-full rounded-xl border border-slate-200 py-2.5 pl-9"
          />
        </div>
        <select
          value={filter}
          onChange={(event) => {
            setFilter(event.target.value as "" | "0" | "1");
            setPage(1);
          }}
          className="rounded-xl border border-slate-200 px-3"
        >
          <option value="">All model classes</option>
          <option value="1">Model class 1</option>
          <option value="0">Model class 0</option>
        </select>
      </div>
      {loading && !data ? (
        <div className="mt-5">
          <Notice
            title="Loading history"
            message="Getting records from the API."
          />
        </div>
      ) : error && !data ? (
        <div className="mt-5">
          <Notice
            title="History unavailable"
            message={error}
            retry={() => void load()}
          />
        </div>
      ) : (
        <div className="mt-5">
          <p className="mb-3 text-sm text-slate-500">
            {data?.total_count ?? 0} matching records
          </p>
          <Records records={records} preferences={preferences} />
          {records.length > 0 && (
            <div className="mt-3 flex items-center justify-between">
              <p className="text-xs text-slate-500">
                Page {page} of {totalPages}
              </p>
              <div className="flex gap-2">
                <button
                  aria-label="Previous page"
                  disabled={page === 1}
                  onClick={() => setPage(page - 1)}
                  className="rounded-lg border p-2 disabled:opacity-40"
                >
                  <ChevronLeft size={16} />
                </button>
                <button
                  aria-label="Next page"
                  disabled={page >= totalPages}
                  onClick={() => setPage(page + 1)}
                  className="rounded-lg border p-2 disabled:opacity-40"
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
// PreferencesPage: local display settings for glucose unit, compact tables, and assessment notifications, persisted via the API.
function PreferencesPage({
  preferences,
  reload,
}: {
  preferences: Preferences;
  reload: () => void;
}) {
  const [draft, setDraft] = useState(preferences);
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);
  useEffect(() => setDraft(preferences), [preferences]);
  async function save() {
    setSaving(true);
    setMessage("");
    try {
      await glucocareApi.updatePreferences({
        glucose_unit: draft.glucose_unit,
        compact_tables: draft.compact_tables,
        assessment_notifications: draft.assessment_notifications,
      });
      setMessage("Preferences saved.");
      reload();
    } catch (caught) {
      setMessage(
        caught instanceof ApiError
          ? caught.message
          : "Preferences could not be saved.",
      );
    } finally {
      setSaving(false);
    }
  }
  const toggle = (key: "compact_tables" | "assessment_notifications") =>
    setDraft((current) => ({ ...current, [key]: !current[key] }));
  return (
    <div className="mx-auto max-w-3xl">
      <h2 className="text-2xl font-extrabold text-blue-950">Preferences</h2>
      <p className="mt-1 text-slate-500">
        Persisted in the local development database.
      </p>
      <div className="mt-6 divide-y rounded-2xl border border-blue-100 bg-white p-5 shadow-soft">
        <Setting
          label="Assessment notifications"
          description="Show a success confirmation after saving an assessment."
          value={draft.assessment_notifications}
          onClick={() => toggle("assessment_notifications")}
        />
        <Setting
          label="Compact tables"
          description="Use compact overview table rows."
          value={draft.compact_tables}
          onClick={() => toggle("compact_tables")}
        />
        <label className="flex items-center justify-between gap-4 py-4">
          <span>
            <b className="text-sm text-slate-700">Glucose display unit</b>
            <small className="mt-1 block text-slate-400">
              Converts saved-record displays; assessment inputs remain mg/dL.
            </small>
          </span>
          <select
            value={draft.glucose_unit}
            onChange={(event) =>
              setDraft((current) => ({
                ...current,
                glucose_unit: event.target.value as Preferences["glucose_unit"],
              }))
            }
            className="rounded-xl border px-3 py-2"
          >
            <option>mg/dL</option>
            <option>mmol/L</option>
          </select>
        </label>
      </div>
      <div className="mt-5 flex items-center justify-between">
        <p role="status" className="text-sm text-slate-500">
          {message}
        </p>
        <button
          disabled={saving}
          onClick={() => void save()}
          className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-bold text-white"
        >
          <Check size={16} />
          {saving ? "Saving…" : "Save preferences"}
        </button>
      </div>
    </div>
  );
}
// Setting: accessible toggle switch row for a boolean preference with label and description.
function Setting({
  label,
  description,
  value,
  onClick,
}: {
  label: string;
  description: string;
  value: boolean;
  onClick: () => void;
}) {
  return (
    <div className="flex items-center justify-between gap-4 py-4">
      <span>
        <b className="text-sm text-slate-700">{label}</b>
        <small className="mt-1 block text-slate-400">{description}</small>
      </span>
      <button
        aria-label={label}
        role="switch"
        aria-checked={value}
        onClick={onClick}
        className={cn(
          "h-6 w-11 rounded-full p-0.5",
          value ? "bg-blue-600" : "bg-slate-200",
        )}
      >
        <span
          className={cn(
            "block h-5 w-5 rounded-full bg-white transition-transform",
            value && "translate-x-5",
          )}
        />
      </button>
    </div>
  );
}
// App: root component wiring API resources and preferences into the routed Shell layout across dashboard, assessment, history, and settings.
export default function App() {
  const dashboard = useApiResource(glucocareApi.getDashboard, []);
  const preferenceResource = useApiResource(glucocareApi.getPreferences, []);
  const preferences = preferenceResource.data ?? {
    scope: "local-development",
    glucose_unit: "mg/dL" as const,
    compact_tables: false,
    assessment_notifications: true,
  };
  return (
    <Shell>
      <Routes>
        <Route
          path="/"
          element={<Dashboard resource={dashboard} preferences={preferences} />}
        />
        <Route
          path="/assessment"
          element={
            <Assessment
              onSaved={() => void dashboard.refresh()}
              notifications={preferences.assessment_notifications}
            />
          }
        />
        <Route
          path="/lifestyle-assessment"
          element={<LifestyleAssessment />}
        />
        <Route
          path="/history"
          element={<History preferences={preferences} />}
        />
        <Route
          path="/settings"
          element={
            preferenceResource.loading && !preferenceResource.data ? (
              <Notice
                title="Loading preferences"
                message="Getting saved display settings."
              />
            ) : preferenceResource.error && !preferenceResource.data ? (
              <Notice
                title="Preferences unavailable"
                message={preferenceResource.error}
                retry={() => void preferenceResource.refresh()}
              />
            ) : (
              <PreferencesPage
                preferences={preferences}
                reload={() => void preferenceResource.refresh()}
              />
            )
          }
        />
        <Route
          path="*"
          element={<Dashboard resource={dashboard} preferences={preferences} />}
        />
      </Routes>
    </Shell>
  );
}
