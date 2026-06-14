export interface User {
  id: number;
  email: string;
  first_name: string | null;
  last_name: string | null;
  full_name: string;
  organization_id: number;
  role: { id: number; name: string } | null;
}

export interface Organization {
  id: number;
  uuid: string;
  name: string;
  slug: string;
  plan: string;
  is_white_label: boolean;
  branding_primary_color: string | null;
  branding_logo_url: string | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface Topic {
  id: number;
  name: string;
  description: string | null;
  status: string;
  sources: TopicSource[];
  created_at: string;
}

export interface TopicSource {
  id: number;
  source_type: string;
  name: string;
  query: string | null;
  platform: string | null;
  fetch_status: string;
}

export interface Provider {
  id: number;
  name: string;
  provider_type: string;
  is_active: boolean;
  api_base: string | null;
  api_version: string | null;
  region: string | null;
  config: Record<string, unknown> | null;
  models: ProviderModel[];
}

export interface AzureProviderConfig {
  deployment?: string;
  api_pattern?: "azure_openai_legacy" | "azure_openai_v1" | "azure_responses" | "azure_ai_foundry";
  use_responses_api?: boolean;
  model_name?: string;
  responses_api_version?: string;
  v1_api_version?: string;
  reasoning_effort?: "low" | "medium" | "high";
  verbosity?: "low" | "medium" | "high";
}

export interface ProviderModel {
  id: number;
  external_id: string;
  name: string;
  input_cost_per_1k: number;
  output_cost_per_1k: number;
}

export interface Report {
  id: number;
  title: string;
  format: string;
  status: string;
  download_url: string | null;
  created_at: string;
}

export interface Schedule {
  id: number;
  name: string;
  job_type: string;
  cron_expression: string;
  is_active: boolean;
}

export interface AlertRule {
  id: number;
  name: string;
  entity_type: string;
  metric: string;
  condition: string;
  threshold: number;
  is_active: boolean;
}

export interface Alert {
  id: number;
  title: string;
  severity: string;
  status: string;
  created_at: string;
}

export interface Competitor {
  id: number;
  name: string;
  website_url: string | null;
  industry: string | null;
}
