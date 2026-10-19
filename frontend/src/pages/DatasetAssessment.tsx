import { useState, type FormEvent } from "react";
import { Activity, Check, ShieldCheck } from "lucide-react";
import { ApiError } from "../api/client";
import { glucocareApi } from "../api/glucocare";
import type { DatasetAssessmentInput, DatasetPredictionResponse } from "../api/types";

const fieldClass = "mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-blue-950 outline-none focus:border-blue-400 focus:ring-4 focus:ring-blue-50";
const initial: Record<keyof DatasetAssessmentInput, string> = {
  gender: "Female", age: "40", physical_activity: "Moderate",
  smoking_status: "Never", alcohol_intake: "Occasional", glucose: "110",
  blood_pressure: "75", skin_thickness: "22", insulin: "90", bmi: "27.5",
  cholesterol: "190", diabetes_pedigree_function: "0.45",
  family_history: "No", hypertension: "No",
};
const numericFields: Array<{ key: keyof DatasetAssessmentInput; label: string; min: number; max: number; step?: string; unit?: string }> = [
  { key: "age", label: "Age", min: 1, max: 120, unit: "years" },
  { key: "glucose", label: "Glucose", min: 0, max: 500, unit: "dataset units" },
  { key: "blood_pressure", label: "Blood pressure", min: 0, max: 300, unit: "dataset units" },
  { key: "skin_thickness", label: "Skin thickness", min: 0, max: 150, unit: "dataset units" },
  { key: "insulin", label: "Insulin", min: 0, max: 2000, unit: "dataset units" },
  { key: "bmi", label: "BMI", min: 0.1, max: 100, step: "0.1", unit: "kg/m²" },
  { key: "cholesterol", label: "Cholesterol", min: 0, max: 1000, unit: "dataset units" },
  { key: "diabetes_pedigree_function", label: "Diabetes pedigree function", min: 0, max: 10, step: "0.001" },
];
const selectFields = [
  { key: "gender", label: "Gender", options: ["Female", "Male"] },
  { key: "physical_activity", label: "Physical activity", options: ["Low", "Moderate", "High"] },
  { key: "smoking_status", label: "Smoking status", options: ["Never", "Former", "Current"] },
  { key: "alcohol_intake", label: "Alcohol intake", options: ["Occasional", "Regular"] },
  { key: "family_history", label: "Family history", options: ["No", "Yes"] },
  { key: "hypertension", label: "Hypertension", options: ["No", "Yes"] },
] as const;

export default function DatasetAssessment() {
  const [values, setValues] = useState(initial);
  const [result, setResult] = useState<DatasetPredictionResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const update = (key: keyof DatasetAssessmentInput, value: string) => {
    setValues((current) => ({ ...current, [key]: value }));
    setError("");
    setResult(null);
  };
  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true); setError(""); setResult(null);
    try {
      const payload = {
        gender: values.gender as DatasetAssessmentInput["gender"],
        age: Number(values.age),
        physical_activity: values.physical_activity as DatasetAssessmentInput["physical_activity"],
        smoking_status: values.smoking_status as DatasetAssessmentInput["smoking_status"],
        alcohol_intake: values.alcohol_intake as DatasetAssessmentInput["alcohol_intake"],
        glucose: Number(values.glucose), blood_pressure: Number(values.blood_pressure),
        skin_thickness: Number(values.skin_thickness), insulin: Number(values.insulin),
        bmi: Number(values.bmi), cholesterol: Number(values.cholesterol),
        diabetes_pedigree_function: Number(values.diabetes_pedigree_function),
        family_history: values.family_history as DatasetAssessmentInput["family_history"],
        hypertension: values.hypertension as DatasetAssessmentInput["hypertension"],
      } satisfies DatasetAssessmentInput;
      setResult(await glucocareApi.predictDatasetAssessment(payload));
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "The model request failed. Check that the backend is running and the model is trained.");
    } finally { setBusy(false); }
  }
  const selectValue = (key: keyof DatasetAssessmentInput) => values[key];
  return <div className="mx-auto max-w-5xl">
    <div className="mb-6"><p className="text-xs font-bold uppercase tracking-widest text-blue-600">Uploaded dataset · 20,000 records</p><h2 className="mt-1 text-2xl font-extrabold text-blue-950">Dataset-based assessment</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">This separate assessment uses the uploaded dataset's 14 feature columns and its Diabetic/Non-diabetic target. It does not replace the existing Pima model or the CDC lifestyle model.</p></div>
    <form onSubmit={submit} className="grid gap-6 lg:grid-cols-[1fr_300px]">
      <section className="rounded-2xl border border-blue-100 bg-white p-5 shadow-soft sm:p-7">
        <h3 className="font-bold text-blue-950">Measurements and indicators</h3>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          {selectFields.map((field) => <label key={field.key} className="text-sm font-semibold text-slate-700">{field.label}<select className={fieldClass} value={selectValue(field.key)} onChange={(e) => update(field.key, e.target.value)}>{field.options.map((option) => <option key={option}>{option}</option>)}</select></label>)}
          {numericFields.map((field) => <label key={field.key} className="text-sm font-semibold text-slate-700">{field.label}{field.unit && <span className="float-right text-xs font-normal text-slate-400">{field.unit}</span>}<input className={fieldClass} type="number" min={field.min} max={field.max} step={field.step ?? "1"} required value={values[field.key]} onChange={(e) => update(field.key, e.target.value)} /></label>)}
        </div>
        {error && <p role="alert" className="mt-5 rounded-xl border border-rose-100 bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
        <div className="mt-6 flex items-center justify-between border-t border-slate-100 pt-5"><button type="button" onClick={() => { setValues(initial); setResult(null); setError(""); }} className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-bold text-slate-600">Reset</button><button disabled={busy} className="rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-bold text-white disabled:opacity-60">{busy ? "Evaluating…" : "Run dataset model"}</button></div>
      </section>
      <aside className="space-y-4">
        {result ? <div className="rounded-2xl border border-blue-100 bg-white p-5 shadow-soft"><p className="text-xs font-bold uppercase tracking-wider text-slate-400">Model output</p><h3 className="mt-3 text-2xl font-extrabold text-blue-950">{result.prediction_label}</h3><p className="mt-2 text-sm text-slate-600">Estimated positive-class probability: {(result.probability * 100).toFixed(1)}%</p><div className="mt-3 h-2 overflow-hidden rounded-full bg-blue-50"><div className="h-full rounded-full bg-blue-600" style={{ width: `${result.probability * 100}%` }} /></div><p className="mt-3 text-xs text-slate-500">Model: {result.model_name}</p><p className="mt-2 text-xs text-slate-500">Holdout ROC-AUC: {typeof result.metrics.roc_auc === "number" ? result.metrics.roc_auc.toFixed(3) : "not available"}</p><p className="mt-4 text-xs leading-5 text-slate-500">{result.disclaimer}</p></div> : <div className="rounded-2xl border border-dashed border-blue-200 bg-white p-6 text-center"><Activity className="mx-auto text-blue-500" size={25}/><p className="mt-3 font-bold text-blue-950">Result appears here</p><p className="mt-1 text-xs leading-5 text-slate-500">No model result is fabricated in the browser; predictions come from the backend API.</p></div>}
        <div className="rounded-2xl border border-amber-100 bg-amber-50 p-4"><ShieldCheck size={18} className="text-amber-700"/><p className="mt-2 text-xs leading-5 text-amber-900"><b>Research prototype only.</b> Dataset labels and performance require independent review. This tool cannot diagnose, exclude, or guide treatment for diabetes.</p></div>
      </aside>
    </form>
  </div>;
}
