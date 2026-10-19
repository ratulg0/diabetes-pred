// Shared TypeScript types mirroring the backend API schemas: assessment input,
// model metadata, records, dashboard summary, preferences, and error body.
// Request schema for the replacement 20,000-row clinical-assessment dataset.
export type AssessmentInput = {
  gender: string;
  age: number;
  physical_activity: string;
  smoking_status: string;
  alcohol_intake: string | null;
  glucose: number | null;
  blood_pressure: number | null;
  skin_thickness: number | null;
  insulin: number | null;
  bmi: number | null;
  cholesterol: number | null;
  diabetes_pedigree_function: number | null;
  family_history: string;
  hypertension: string;
};

export type ModelIdentity = { name: string; version: string };

export type ModelCandidateResult = {
  name: string;
  cv_accuracy_mean: number;
  cv_accuracy_std: number;
  cv_roc_auc_mean: number;
  cv_roc_auc_std: number;
  cv_brier_mean: number;
  cv_brier_std: number;
};

export type ModelMetadata = {
  name?: string;
  version?: string;
  algorithm?: string;
  members?: string[];
  ensemble_rule?: string;
  candidate_results?: ModelCandidateResult[];
  test_metrics?: { accuracy?: number; roc_auc?: number; pr_auc?: number };
};

export type AssessmentRecord = {
  prediction_id: string;
  predicted_class: 0 | 1;
  prediction_label: string;
  probability: number | null;
  model_accuracy: number | null;
  model: ModelIdentity;
  disclaimer: string;
  created_at: string;
  source: string;
  input: Partial<AssessmentInput> & { age?: number; glucose?: number | null; pregnancies?: number; legacy_schema?: string; [key: string]: unknown };
};

export type LifestyleAssessmentInput = {
  high_bp: number;
  high_chol: number;
  chol_check: number;
  bmi: number;
  smoker: number;
  stroke: number;
  heart_disease_or_attack: number;
  phys_activity: number;
  fruits: number;
  veggies: number;
  hvy_alcohol_consump: number;
  any_healthcare: number;
  no_docbc_cost: number;
  gen_hlth: number;
  ment_hlth: number;
  phys_hlth: number;
  diff_walk: number;
  sex: number;
  age: number;
  education: number;
  income: number;
};

export type LifestyleAssessmentRecord = {
  prediction_id: string;
  predicted_class: 0 | 1;
  prediction_label: string;
  probability: number | null;
  model_accuracy: number | null;
  model: ModelIdentity;
  target_definition: string;
  disclaimer: string;
  created_at: string;
  source: string;
  input: LifestyleAssessmentInput;
};

export type LifestyleAssessmentPage = {
  items: LifestyleAssessmentRecord[];
  page: number;
  page_size: number;
  total_count: number;
};

export type AssessmentPage = {
  items: AssessmentRecord[];
  page: number;
  page_size: number;
  total_count: number;
};

export type DashboardSummary = {
  total_assessments: number;
  higher_class_assessments: number;
  recent_assessments: AssessmentRecord[];
};

export type Preferences = {
  scope: string;
  glucose_unit: "mg/dL" | "mmol/L";
  compact_tables: boolean;
  assessment_notifications: boolean;
};

export type ModelStatus = {
  available: boolean;
  metadata: ModelMetadata | null;
  reason: string | null;
};

export type ApiErrorBody = {
  code?: string;
  message?: string;
  request_id?: string;
  field_errors?: Record<string, string>;
};

