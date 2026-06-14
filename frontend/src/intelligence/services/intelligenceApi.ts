import api from "@/services/api";

export interface IntelligenceToday {
  enabled: boolean;
  message?: string;
  alerts?: { count: number; new: number };
  opportunities?: { count: number; urgent: number };
  threats?: { count: number; entities: unknown[] };
  workflows?: { active: number };
  priority_queue?: ActionItem[];
  recent_events?: IntelligenceEvent[];
}

export interface ActionItem {
  id: string;
  type: string;
  title: string;
  description?: string;
  why_matters?: string;
  expected_outcome?: string;
  urgency: number;
  effort: number;
  impact_score: number;
  priority_score?: number;
  source_modules?: string[];
  related_entities?: RelatedEntity[];
  suggested_actions?: SuggestedAction[];
  status?: string;
}

export interface SuggestedAction {
  id: string;
  type: string;
  title: string;
}

export interface RelatedEntity {
  id: string;
  type: string;
  name: string;
  relationship?: string;
}

export interface IntelligenceEvent {
  id: string;
  type: string;
  source: string;
  payload: Record<string, unknown>;
  priority: string;
  timestamp: string;
}

export interface EntityIntelligence {
  entity?: Record<string, unknown>;
  related_entities?: RelatedEntity[];
  timeline?: IntelligenceEvent[];
  recommended_actions?: ActionItem[];
}

export const intelligenceApi = {
  getToday: () => api.get<IntelligenceToday>("/intelligence/today"),

  getEntity: (type: string, id: string) =>
    api.get<EntityIntelligence>(`/intelligence/entity/${type}/${id}`),

  getBrief: (type: string) => api.get<Record<string, unknown>>(`/intelligence/brief/${type}`),

  listActions: (status = "pending", limit = 50) =>
    api.get<{ status?: string; actions: ActionItem[] }>(
      `/intelligence/actions?status=${status}&limit=${limit}`
    ),

  executeAction: (actionId: string, params: Record<string, unknown> = {}) =>
    api.post(`/intelligence/actions/${actionId}/execute`, params),

  dismissAction: (actionId: string, reason: string) =>
    api.post(`/intelligence/actions/${actionId}/dismiss`, { reason }),

  createAction: (actionData: Record<string, unknown>) =>
    api.post("/intelligence/action", actionData),

  listWorkflows: (status?: string) =>
    api.get<Record<string, unknown>>(
      `/intelligence/workflows?status=${status || ""}`
    ),

  search: (query: string) =>
    api.get<Record<string, unknown>>(
      `/intelligence/search?q=${encodeURIComponent(query)}`
    ),

  health: () => api.get<Record<string, unknown>>("/health/intelligence"),
};
