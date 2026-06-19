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
  features: CompetitorFeature[] | null;
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

export interface CompetitorFeature {
  name: string;
  description: string | null;
  evidence: string | null;
  confidence: string | null;
}

export interface CompetitorComparisonSource {
  name: string;
  source_type: string;
  url: string | null;
}

export interface Competitor {
  id: number;
  name: string;
  website_url: string | null;
  industry: string | null;
  description: string | null;
  social_handles: string | null;
  is_active: boolean;
  organization_id: number;
  created_at: string;
  updated_at: string;
}

export interface CompetitorFeatureComparison {
  id: number;
  title: string;
  status: string;
  report_format: string;
  markdown_content: string | null;
  download_url: string | null;
  our_features: CompetitorFeature[] | null;
  their_features: CompetitorFeature[] | null;
  comparison_summary: string | null;
  sources: CompetitorComparisonSource[] | null;
  created_at: string;
  updated_at: string;
}

export interface IntelligenceSource {
  id: number;
  source_type: string;
  name: string;
  url: string | null;
  query: string | null;
  configuration: Record<string, unknown> | null;
  refresh_interval_minutes: number | null;
  is_active: boolean;
  status: string;
  fetch_error: string | null;
  last_fetched_at: string | null;
  competitor_id: number | null;
  topic_id: number | null;
  organization_id: number;
  created_at: string;
  updated_at: string;
}

export interface IntelligenceItem {
  id: number;
  item_type: string;
  title: string;
  content: string | null;
  summary: string | null;
  url: string | null;
  source_name: string | null;
  source_url: string | null;
  published_at: string | null;
  fetched_at: string;
  relevance_score: number | null;
  sentiment: string | null;
  tags: string[] | null;
  entities: { type: string; name: string }[] | null;
  metadata: Record<string, unknown> | null;
  is_noise: boolean;
  competitor_id: number | null;
  topic_id: number | null;
  source_id: number | null;
  organization_id: number;
  created_at: string;
  updated_at: string;
}

export interface FactTemplate {
  id: number;
  fact_type: string;
  name: string;
  description: string | null;
  prompt: string | null;
  schema_definition: Record<string, unknown> | null;
  example: Record<string, unknown> | null;
  is_system: boolean;
  is_active: boolean;
  organization_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface FactEvidence {
  source_name: string | null;
  url: string | null;
  quote: string | null;
}

export interface AskSource {
  chunk_type: string;
  title: string | null;
  url: string | null;
  content: string | null;
  score: number | null;
}

export interface AskResponse {
  question: string;
  answer: string;
  sources: AskSource[];
}

export interface Integration {
  id: number;
  integration_type: string;
  name: string;
  is_active: boolean;
  config: Record<string, unknown> | null;
  organization_id: number;
  created_at: string;
  updated_at: string;
}

export interface NewsletterIssue {
  id: number;
  schedule_id: number | null;
  title: string;
  content_markdown: string;
  content_html: string | null;
  status: string;
  sent_at: string | null;
  recipient_count: number | null;
  organization_id: number;
  created_at: string;
  updated_at: string;
}

export interface NewsletterSchedule {
  id: number;
  name: string;
  cron_expression: string;
  timezone: string;
  is_active: boolean;
  configuration: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface Fact {
  id: number;
  fact_type: string;
  title: string;
  summary: string | null;
  attributes: Record<string, unknown> | null;
  confidence: string | null;
  evidence: FactEvidence[] | null;
  effective_date: string | null;
  verified_at: string | null;
  verified_by_user_id: number | null;
  competitor_id: number | null;
  item_id: number | null;
  template_id: number | null;
  organization_id: number;
  created_at: string;
  updated_at: string;
}

export interface DailyCost {
  date: string;
  input_cost: number;
  output_cost: number;
  total_cost: number;
  total_tokens: number;
}

export interface ProviderCost {
  provider_type: string;
  total_cost: number;
  total_tokens: number;
}

export interface UsageCostsResponse {
  daily: DailyCost[];
  by_provider: ProviderCost[];
}

export interface DashboardStats {
  topics: number;
  competitors: number;
  sources: number;
  alert_rules: number;
  open_alerts: number;
  items: number;
  facts: number;
}

export interface DashboardSnapshot {
  stats: DashboardStats;
  costs: UsageCostsResponse | null;
}

export interface DashboardEvent {
  type: string;
  data: DashboardSnapshot;
}
