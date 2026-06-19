import { CONFIG } from "@/config";
import type { DashboardSnapshot, Provider, UsageCostsResponse } from "@/types";
import axios, { AxiosError } from "axios";

const api = axios.create({
  baseURL: `${CONFIG.apiUrl}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;

export const authApi = {
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }),
  register: (data: {
    email: string;
    password: string;
    first_name?: string;
    organization_name?: string;
  }) => api.post("/auth/register", data),
  me: () => api.get("/auth/me"),
};

export const organizationApi = {
  me: () => api.get("/organizations/me"),
  updateFeatures: (features: { name: string; description?: string | null }[]) =>
    api.put("/organizations/me", { features }),
};

export const topicsApi = {
  list: () => api.get("/topics"),
  create: (data: { name: string; description?: string }) =>
    api.post("/topics", data),
  get: (id: number) => api.get(`/topics/${id}`),
  analyze: (id: number, data: { analysis_types: string[] }) =>
    api.post(`/topics/${id}/analyze`, data),
  runs: (id: number) => api.get(`/topics/${id}/runs`),
  addSource: (id: number, data: {
    source_type: string;
    name: string;
    query?: string;
    platform?: string;
  }) => api.post(`/topics/${id}/sources`, data),
};

export interface ProviderCreatePayload {
  name: string;
  provider_type: string;
  api_key?: string;
  api_base?: string;
  api_version?: string;
  region?: string;
  config?: Record<string, unknown>;
  models: { external_id: string; name: string }[];
}

export interface ProviderUpdatePayload {
  name?: string;
  api_key?: string;
  api_base?: string;
  api_version?: string;
  region?: string;
  is_active?: boolean;
  config?: Record<string, unknown> | null;
}

export const providersApi = {
  list: () => api.get<Provider[]>("/providers"),
  create: (data: ProviderCreatePayload) => api.post("/providers", data),
  get: (id: number) => api.get<Provider>(`/providers/${id}`),
  update: (id: number, data: ProviderUpdatePayload) =>
    api.put<Provider>(`/providers/${id}`, data),
  delete: (id: number) => api.delete(`/providers/${id}`),
  test: (id: number) => api.post(`/providers/${id}/test`, {}),
  types: () => api.get("/providers/types"),
};

export const reportsApi = {
  list: () => api.get("/reports"),
  create: (data: {
    title: string;
    report_type: string;
    format: string;
    topic_id: number;
  }) => api.post("/reports", data),
};

export const schedulesApi = {
  list: () => api.get("/schedules"),
  create: (data: {
    name: string;
    job_type: string;
    cron_expression: string;
    timezone?: string;
    topic_id?: number;
    configuration?: Record<string, unknown>;
  }) => api.post("/schedules", data),
};

export const alertRulesApi = {
  list: () => api.get("/alert-rules"),
  create: (data: {
    name: string;
    entity_type: string;
    condition: string;
    threshold: number;
    metric: string;
    topic_id?: number;
    notification_channels?: string;
  }) => api.post("/alert-rules", data),
};

export const alertsApi = {
  list: () => api.get("/alerts"),
};

export const competitorsApi = {
  list: () => api.get("/competitors"),
  create: (data: { name: string; website_url?: string; industry?: string; social_handles?: string }) =>
    api.post("/competitors", data),
  compare: (id: number, data?: { title?: string; report_format?: string }) =>
    api.post(`/competitors/${id}/compare`, data),
  comparisons: (id: number) => api.get(`/competitors/${id}/comparisons`),
  latestComparison: (id: number) =>
    api.get(`/competitors/${id}/comparisons/latest`),
  downloadComparison: (comparisonId: number) =>
    api.get(`/competitors/comparisons/${comparisonId}/download`, {
      responseType: "blob",
    }),
};

export const intelligenceSourcesApi = {
  list: () => api.get("/intelligence/sources"),
  create: (data: {
    source_type: string;
    name: string;
    url?: string;
    query?: string;
    configuration?: Record<string, unknown>;
    refresh_interval_minutes?: number;
    competitor_id?: number;
    topic_id?: number;
  }) => api.post("/intelligence/sources", data),
  ingest: (id: number) => api.post(`/intelligence/sources/${id}/ingest`, {}),
  delete: (id: number) => api.delete(`/intelligence/sources/${id}`),
};

export const intelligenceItemsApi = {
  list: (params?: {
    item_type?: string;
    competitor_id?: number;
    topic_id?: number;
    sentiment?: string;
    tag?: string;
    is_noise?: boolean;
  }) => api.get("/intelligence/items", { params }),
};

export const factsApi = {
  list: (params?: {
    fact_type?: string;
    competitor_id?: number;
    confidence?: string;
  }) => api.get("/facts", { params }),
  templates: () => api.get("/facts/templates"),
  extract: (itemId: number, factTypes?: string[]) =>
    api.post("/facts/extract", { item_id: itemId, fact_types: factTypes }),
};

export const askApi = {
  ask: (question: string, topK: number = 5, providerId?: number | null) =>
    api.post("/intelligence/ask", {
      question,
      top_k: topK,
      provider_id: providerId,
    }),
};

export const integrationsApi = {
  list: (params?: { integration_type?: string }) =>
    api.get("/integrations", { params }),
  create: (data: {
    integration_type: string;
    name: string;
    config?: Record<string, unknown>;
    credentials?: string;
  }) => api.post("/integrations", data),
  update: (id: number, data: {
    name?: string;
    is_active?: boolean;
    config?: Record<string, unknown>;
    credentials?: string;
  }) => api.put(`/integrations/${id}`, data),
  delete: (id: number) => api.delete(`/integrations/${id}`),
  test: (id: number) => api.post(`/integrations/${id}/test`, {}),
};

export const newslettersApi = {
  list: () => api.get("/newsletters"),
  get: (id: number) => api.get(`/newsletters/${id}`),
  create: (data: {
    title?: string;
    integration_ids?: number[];
    email_recipients?: string[];
    topic_ids?: number[];
    competitor_ids?: number[];
    since_hours?: number;
    send_now?: boolean;
  }) => api.post("/newsletters", data),
  send: (id: number, data: {
    integration_ids?: number[];
    email_recipients?: string[];
  }) => api.post(`/newsletters/${id}/send`, data),
  schedules: () => api.get("/newsletters/schedules"),
};

export const usageApi = {
  costs: (days: number = 30) =>
    api.get<UsageCostsResponse>("/usage/costs", { params: { days } }),
};

export const dashboardApi = {
  snapshot: () => api.get<DashboardSnapshot>("/dashboard/snapshot"),
};
