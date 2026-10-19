export type AssessmentInput = {
  pregnancies: number;
  glucose: number;
  blood_pressure: number;
  skin_thickness: number;
  insulin: number;
  bmi: number;
  diabetes_pedigree_function: number;
  age: number;
};

export type ModelIdentity = { name: string; version: string };

export type AssessmentRecord = {
  prediction_id: string;
  predicted_class: 0 | 1;
  probability: number | null;
  model: ModelIdentity;
  disclaimer: string;
  created_at: string;
  source: string;
  input: AssessmentInput;
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
  metadata: Record<string, unknown> | null;
  reason: string | null;
};

export type ApiErrorBody = {
  code?: string;
  message?: string;
  request_id?: string;
  field_errors?: Record<string, string>;
};
