import { useEffect, useState, type FormEvent } from "react";
import { Activity, ChevronLeft, ChevronRight, HeartPulse, Info, LoaderCircle, ShieldCheck } from "lucide-react";
import { ApiError } from "../api/client";
import { glucocareApi } from "../api/glucocare";
import type { LifestyleAssessmentInput, LifestyleAssessmentRecord } from "../api/types";
type Field = { key: string; label: string; help: string; min: number; max: number; options?: Array<[number, string]> };
const yn: Array<[number, string]> = [[0, "No"], [1, "Yes"]];
const fields: Field[] = [
  { key: "high_bp", label: "High blood pressure", help: "Ever told you have high blood pressure?", min: 0, max: 1, options: yn },
  { key: "high_chol", label: "High cholesterol", help: "Ever told your cholesterol is high?", min: 0, max: 1, options: yn },
  { key: "chol_check", label: "Cholesterol check", help: "Cholesterol checked in the past five years?", min: 0, max: 1, options: yn },
  { key: "bmi", label: "BMI", help: "Body mass index (kg/m²).", min: 10, max: 100 },
  { key: "smoker", label: "Smoking history", help: "Smoked at least 100 cigarettes in your life?", min: 0, max: 1, options: yn },
  { key: "stroke", label: "History of stroke", help: "Ever told you had a stroke?", min: 0, max: 1, options: yn },
  { key: "heart_disease_or_attack", label: "Heart disease or heart attack", help: "Ever told you had coronary heart disease or a heart attack?", min: 0, max: 1, options: yn },
  { key: "phys_activity", label: "Physical activity", help: "Exercise outside your regular job in the past 30 days?", min: 0, max: 1, options: yn },
  { key: "fruits", label: "Daily fruit consumption", help: "Consume fruit one or more times per day?", min: 0, max: 1, options: yn },
  { key: "veggies", label: "Daily vegetable consumption", help: "Consume vegetables one or more times per day?", min: 0, max: 1, options: yn },
  { key: "hvy_alcohol_consump", label: "Heavy alcohol consumption", help: "CDC survey-coded indicator.", min: 0, max: 1, options: yn },
  { key: "any_healthcare", label: "Healthcare coverage", help: "Do you have any healthcare coverage?", min: 0, max: 1, options: yn },
  { key: "no_docbc_cost", label: "Skipped care due to cost", help: "Could not see a doctor in the past year because of cost?", min: 0, max: 1, options: yn },
  { key: "gen_hlth", label: "General health", help: "Self-reported health.", min: 1, max: 5, options: [[1, "Excellent"], [2, "Very good"], [3, "Good"], [4, "Fair"], [5, "Poor"]] },
  { key: "ment_hlth", label: "Days mental health was not good", help: "Days in the past 30 days.", min: 0, max: 30 },
  { key: "phys_hlth", label: "Days physical health was not good", help: "Days in the past 30 days.", min: 0, max: 30 },
  { key: "diff_walk", label: "Difficulty walking", help: "Serious difficulty walking or climbing stairs?", min: 0, max: 1, options: yn },
  { key: "sex", label: "Sex category (source coding)", help: "Original dataset coding: 0 female, 1 male.", min: 0, max: 1, options: [[0, "Female (code 0)"], [1, "Male (code 1)"]] },
  { key: "age", label: "Age category", help: "Age band, not exact age.", min: 1, max: 13, options: [[1, "18–24"], [2, "25–29"], [3, "30–34"], [4, "35–39"], [5, "40–44"], [6, "45–49"], [7, "50–54"], [8, "55–59"], [9, "60–64"], [10, "65–69"], [11, "70–74"], [12, "75–79"], [13, "80+"]] },
  { key: "education", label: "Education category", help: "Highest education category in source survey.", min: 1, max: 6, options: [[1, "Never attended / kindergarten"], [2, "Grades 1–8"], [3, "Grades 9–11"], [4, "High school graduate"], [5, "Some college / technical school"], [6, "College graduate"]] },
  { key: "income", label: "Income category", help: "Survey-coded income band.", min: 1, max: 8, options: [[1, "Below $10,000"], [2, "$10,000–$14,999"], [3, "$15,000–$19,999"], [4, "$20,000–$24,999"], [5, "$25,000–$34,999"], [6, "$35,000–$49,999"], [7, "$50,000–$74,999"], [8, "$75,000 or more"]] },
];

export default function LifestyleAssessment() {
  const [values, setValues] = useState<Record<string, string>>({});
  const [result, setResult] = useState<LifestyleAssessmentRecord | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState<LifestyleAssessmentRecord[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    setHistoryLoading(true);
    glucocareApi
      .getLifestyleHistory({ page, pageSize: 20, predictedClass: "" })
      .then((pageData) => {
        setSaved(pageData.items);
        setTotalPages(Math.max(1, Math.ceil(pageData.total_count / 20)));
        setHistoryLoading(false);
      })
      .catch(() => setHistoryLoading(false));
  }, [page]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setResult(null);
    if (fields.some((f) => values[f.key] === undefined || values[f.key] === "")) {
      setError("Please complete every field before running the assessment.");
      return;
    }
    const payload = Object.fromEntries(
      fields.map((f) => [f.key, Number(values[f.key])])
    ) as LifestyleAssessmentInput;
    setBusy(true);
    try {
      const savedRecord = await glucocareApi.saveLifestyle(payload);
      setResult(savedRecord);
      setSaved((current) => [savedRecord, ...current].slice(0, 20));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "The lifestyle model could not run. Check backend and model readiness.");
    } finally {
      setBusy(false);
    }
  }

  const displayDate = (date: string) => new Date(date).toLocaleDateString(undefined, { dateStyle: "medium" });

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-6 rounded-2xl border border-blue-100 bg-gradient-to-r from-blue-50 to-white p-6 sm:p-8">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-blue-600 p-3 text-white">
            <HeartPulse size={24} />
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-blue-600">
              Separate CDC survey model
            </p>
            <h2 className="text-2xl font-extrabold text-blue-950">
              Lifestyle &amp; health indicators
            </h2>
          </div>
        </div>
        <p className="mt-4 text-sm leading-6 text-slate-600">
          Uses health behaviors, self-reported health, and demographic bands from CDC
          Diabetes Health Indicators (UCI ML Repository dataset 891). Independent of
          the clinical lab assessment.
        </p>
        <div className="mt-4 flex gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm leading-5 text-amber-900">
          <Info size={18} className="mt-0.5 shrink-0" />
          <span>
            The source positive target combines prediabetes and diabetes. This is a
            survey-based research estimate, not a confirmed diagnosis.
          </span>
        </div>
      </div>

      <form onSubmit={submit} className="rounded-2xl border border-blue-100 bg-white p-5 shadow-soft sm:p-7">
        <div className="grid gap-5 md:grid-cols-2">
          {fields.map((f) => (
            <label key={f.key} className="block text-sm font-semibold text-slate-700">
              <span>{f.label}</span>
              <span className="mt-1 block text-xs font-normal leading-5 text-slate-400">
                {f.help}
              </span>
              {f.options ? (
                <select
                  required
                  value={values[f.key] ?? ""}
                  onChange={(e) =>
                    setValues((v) => ({ ...v, [f.key]: e.target.value }))}
                  className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5"
                >
                  <option value="" disabled>
                    Select an answer
                  </option>
                  {f.options.map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  required
                  type="number"
                  min={f.min}
                  max={f.max}
                  step="1"
                  value={values[f.key] ?? ""}
                  onChange={(e) =>
                    setValues((v) => ({ ...v, [f.key]: e.target.value }))}
                  className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5"
                />
              )}
            </label>
          ))}
        </div>
        {error && (
          <p role="alert" className="mt-5 rounded-xl bg-rose-50 p-3 text-sm text-rose-800">
            {error}
          </p>
        )}
        <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-5">
          <button
            type="button"
            disabled={busy}
            onClick={() => {
              setValues({});
              setResult(null);
              setError("");
            }}
            className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-bold text-slate-600"
          >
            Clear fields
          </button>
          <button
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-bold text-white disabled:opacity-60"
          >
            {busy ? (
              <LoaderCircle size={16} className="animate-spin" />
            ) : (
              <Activity size={16} />
            )}
            {busy ? "Running model…" : "Run lifestyle assessment"}
          </button>
        </div>
      </form>

      {result && (
        <section
          role="status"
          className="mt-6 rounded-2xl border border-blue-100 bg-white p-6 shadow-soft"
        >
          <p className="text-xs font-bold uppercase tracking-wider text-blue-600">
            Model result (saved)
          </p>
          <h3 className="mt-2 text-xl font-extrabold text-blue-950">
            {result.prediction_label}
          </h3>
          <p className="mt-2 text-sm text-slate-600">
            Estimated probability of dataset positive class:{" "}
            <strong>{((result.probability ?? 0) * 100).toFixed(1)}%</strong>
          </p>
          <p className="mt-2 text-xs text-slate-400">
            Model: {result.model.name} · Version {result.model.version} · Saved{" "}
            {displayDate(result.created_at)}
          </p>
          <div className="mt-4 rounded-xl bg-blue-50 p-3 text-sm leading-5 text-blue-900">
            <ShieldCheck size={17} className="mr-2 inline" />
            {result.target_definition} {result.disclaimer}
          </div>
        </section>
      )}

      <section className="mt-10 rounded-2xl border border-blue-100 bg-white p-6 sm:p-8">
        <p className="text-xs font-bold uppercase tracking-wider text-blue-600 mb-3">
          Saved lifestyle assessments
        </p>
        {historyLoading ? (
          <p className="text-sm text-slate-500">Loading saved assessments…</p>
        ) : saved.length === 0 ? (
          <p className="text-sm text-slate-500">
            No saved lifestyle assessments yet. Run an assessment above to save your
            first record.
          </p>
        ) : (
          <>
            <div className="overflow-x-auto rounded-xl border border-slate-200">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs text-slate-500">
                  <tr>
                    <th className="p-4">ID</th>
                    <th className="p-4">Date</th>
                    <th className="p-4">Result</th>
                    <th className="p-4">Probability</th>
                    <th className="p-4">Model</th>
                  </tr>
                </thead>
                <tbody>
                  {saved.map((record) => (
                    <tr
                      key={record.prediction_id}
                      className="border-t border-slate-100"
                    >
                      <td className="p-4 font-mono text-xs">
                        {record.prediction_id}
                      </td>
                      <td className="p-4">{displayDate(record.created_at)}</td>
                      <td className="p-4 font-semibold">
                        {record.predicted_class === 1 ? "Likely YES" : "Likely NO"}
                      </td>
                      <td className="p-4">
                        {(record.probability ?? 0).toFixed(3)}
                      </td>
                      <td className="p-4 text-xs">{record.model.name}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {saved.length > 0 && (
              <div className="mt-4 flex items-center justify-between">
                <p className="text-xs text-slate-500">
                  Page {page} of {totalPages}
                </p>
                <div className="flex gap-2">
                  <button
                    disabled={page === 1 || historyLoading}
                    onClick={() => setPage((p) => p - 1)}
                    className="rounded-lg border p-2 disabled:opacity-40"
                  >
                    <ChevronLeft size={16} />
                  </button>
                  <button
                    disabled={page >= totalPages || historyLoading}
                    onClick={() => setPage((p) => p + 1)}
                    className="rounded-lg border p-2 disabled:opacity-40"
                  >
                    <ChevronRight size={16} />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
}
