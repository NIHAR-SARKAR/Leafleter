import { CONFIG } from "@/config";
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

export const providersApi = {
  list: () => api.get("/providers"),
  create: (data: ProviderCreatePayload) => api.post("/providers", data),
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

export const competitorsApi = {
  list: () => api.get("/competitors"),
  create: (data: { name: string; website_url?: string }) =>
    api.post("/competitors", data),
};
