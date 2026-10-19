// Frontend API service layer wrapping the request client for each backend
// endpoint under /api/v1.
import { request } from "./client";
import type {
  AssessmentInput,
  AssessmentPage,
  AssessmentRecord,
  DashboardSummary,
  DatasetDistribution,
  LifestyleAssessmentInput,
  LifestyleAssessmentPage,
  LifestyleAssessmentRecord,
  ModelStatus,
  Preferences,
} from "./types";

const API_PREFIX = "/api/v1";

export const glucocareApi = {
  getDashboard: () =>
    request<DashboardSummary>(`${API_PREFIX}/dashboard/summary`),
  getDatasetDistribution: () =>
    request<DatasetDistribution>(`${API_PREFIX}/dashboard/dataset-distribution`),
  getModelStatus: () => request<ModelStatus>(`${API_PREFIX}/models`),
  retrainAllModels: () =>
    request<ModelStatus>(`${API_PREFIX}/models/retrain-all`, { method: "POST" }, 300_000),
  createAssessment: (input: AssessmentInput) =>
    request<AssessmentRecord>(`${API_PREFIX}/assessments`, {
      method: "POST",
      body: JSON.stringify(input),
    }),
  getAssessments: (params: {
    page: number;
    pageSize: number;
    search: string;
    predictedClass: "" | "0" | "1";
  }) => {
    const search = new URLSearchParams({
      page: String(params.page),
      page_size: String(params.pageSize),
    });
    if (params.search.trim()) search.set("search", params.search.trim());
    if (params.predictedClass)
      search.set("predicted_class", params.predictedClass);
    return request<AssessmentPage>(
      `${API_PREFIX}/assessments?${search.toString()}`,
    );
  },
  getPreferences: () => request<Preferences>(`${API_PREFIX}/preferences`),
  updatePreferences: (preferences: Omit<Preferences, "scope">) =>
    request<Preferences>(`${API_PREFIX}/preferences`, {
      method: "PUT",
      body: JSON.stringify(preferences),
    }),
  // Lifestyle assessment endpoints (CDC survey model).
  saveLifestyle: (input: LifestyleAssessmentInput) =>
    request<LifestyleAssessmentRecord>(`${API_PREFIX}/lifestyle-assessments/save`, {
      method: "POST",
      body: JSON.stringify(input),
    }),
  getLifestyleHistory: (params: {
    page: number;
    pageSize: number;
    predictedClass: "" | "0" | "1";
  }) => {
    const search = new URLSearchParams({
      page: String(params.page),
      page_size: String(params.pageSize),
    });
    if (params.predictedClass) search.set("predicted_class", params.predictedClass);
    return request<LifestyleAssessmentPage>(
      `${API_PREFIX}/lifestyle-assessments/history?${search.toString()}`,
    );
  },
};
