export interface User {
  id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  avatar_url: string;
  phone: string;
  timezone: string;
  locale: string;
  email_verified: boolean;
  is_onboarded: boolean;
  tenant_id: string;
  is_active: boolean;
  date_joined: string;
  last_activity_at: string;
}

export interface Contact {
  id: string;
  account: string | null;
  account_name: string;
  first_name: string;
  last_name: string;
  full_name: string;
  email: string;
  phone: string;
  mobile: string;
  job_title: string;
  department: string;
  avatar_url: string;
  linkedin_url: string;
  twitter_handle: string;
  street: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  owner_id: string | null;
  source: string;
  tags: string[];
  custom_fields: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Account {
  id: string;
  name: string;
  domain: string;
  industry: string;
  description: string;
  website: string;
  phone: string;
  address_line1: string;
  address_line2: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  employees_count: number | null;
  annual_revenue: number | null;
  logo_url: string;
  owner_id: string | null;
  tags: string[];
  custom_fields: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Pipeline {
  id: string;
  name: string;
  description: string;
  is_default: boolean;
  is_active: boolean;
  stages: Stage[];
  tenant_id: string;
  created_at: string;
  updated_at: string;
}

export interface Stage {
  id: string;
  pipeline: string;
  name: string;
  display_order: number;
  probability: number;
  color: string;
  is_active: boolean;
  tenant_id: string;
  created_at: string;
  updated_at: string;
}

export type DealStatus = 'open' | 'won' | 'lost' | 'abandoned';

export interface Deal {
  id: string;
  name: string;
  pipeline: string;
  stage: string;
  contact: string | null;
  account: string | null;
  value: number;
  currency: string;
  status: DealStatus;
  probability: number | null;
  expected_close_date: string | null;
  closed_at: string | null;
  close_reason: string;
  owner_id: string | null;
  description: string;
  tags: string[];
  custom_fields: Record<string, unknown>;
  entered_stage_at: string | null;
  win_probability: number;
  weighted_value: number;
  pipeline_name: string;
  stage_name: string;
  contact_name: string;
  account_name: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
}

export type ActivityType = 'note' | 'call' | 'email' | 'meeting' | 'task' | 'deal_stage_change' | 'deal_status_change' | 'file_upload' | 'system';

export interface Activity {
  id: string;
  activity_type: ActivityType;
  title: string;
  description: string;
  entity_type: string;
  entity_id: string;
  metadata: Record<string, unknown>;
  actor_id: string | null;
  duration_minutes: number | null;
  call_outcome: string;
  call_recording_url: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
}

export type EmailDirection = 'inbound' | 'outbound';

export type CustomFieldType = 'text' | 'number' | 'date' | 'select';
export type CustomFieldEntity = 'contacts' | 'deals' | 'accounts';

export interface CustomFieldDef {
  id: string;
  name: string;
  field_type: CustomFieldType;
  entity_type: CustomFieldEntity;
  options: string[];
  is_active: boolean;
  order: number;
  tenant_id: string;
  created_at: string;
  updated_at: string;
}

export interface EmailMessage {
  id: string;
  message_id: string;
  thread_id: string;
  direction: EmailDirection;
  from_email: string;
  to_emails: string[];
  cc_emails: string[];
  bcc_emails: string[];
  subject: string;
  body_text: string;
  body_html: string;
  sent_at: string;
  received_at: string | null;
  is_read: boolean;
  is_starred: boolean;
  labels: string[];
  entity_type: string;
  entity_id: string | null;
  tenant_id: string;
  created_at: string;
  updated_at: string;
}

export type SyncProvider = 'gmail' | 'outlook' | 'google_calendar' | 'outlook_calendar' | 'imap' | 'caldav';
export type SyncConnectionStatus = 'active' | 'error' | 'expired' | 'disconnected' | 'pending';

export interface SyncConnection {
  id: string;
  provider: SyncProvider;
  provider_account: string;
  account_type: string;
  is_active: boolean;
  status: SyncConnectionStatus;
  last_sync_at: string | null;
  last_sync_success: boolean | null;
  last_error_message: string;
  error_count: number;
  sync_interval_seconds: number;
  created_at: string;
  updated_at: string;
}

export interface SyncState {
  id: string;
  sync_type: string;
  provider: string;
  state: string;
  last_full_sync_at: string | null;
  last_delta_sync_at: string | null;
  next_sync_at: string | null;
  total_synced_count: number;
  total_deleted_count: number;
  created_at: string;
  updated_at: string;
}

export interface CalendarAuthStatus {
  connected: boolean;
  email: string;
  last_sync_at: string | null;
  last_sync_success: boolean | null;
  sync_state: string;
  events_count: number;
}

// ── Calendar Event Types (Phase 5) ────────────────────────────────────────

export interface CalendarEventCreatePayload {
  summary: string;
  start: string;
  end: string;
  description?: string;
  location?: string;
  timezone?: string;
  all_day?: boolean;
  attendees?: { email: string; displayName?: string }[];
  source_entity_type?: string;
  source_entity_id?: string;
  link_to_contacts?: string[];
  link_to_deal?: string;
  remind_before_minutes?: number;
}

export interface CalendarEventResponse {
  id: string;
  external_event_id: string;
  html_link: string;
  summary: string;
  start: string;
  end: string;
  status: string;
}

export interface CalendarEventUpdatePayload {
  summary?: string;
  start?: string;
  end?: string;
  description?: string;
  location?: string;
  timezone?: string;
  all_day?: boolean;
  attendees?: { email: string; displayName?: string }[];
}

export interface CalendarWatchStatus {
  connected: boolean;
  push_enabled: boolean;
  watch_channel_id?: string;
  watch_expires_at?: string;
  last_push_received_at?: string;
  fallback_polling_active: boolean;
}

export interface ScopeUpgradeResponse {
  url: string;
  state: string;
  connection_id: string;
}

export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';
export type TaskStatus2 = 'todo' | 'in_progress' | 'done' | 'cancelled';

// ── Audit Log Types (Phase 4 P3) ────────────────────────────────────────

export type AuditAction =
  | 'create' | 'update' | 'delete'
  | 'login' | 'export' | 'import'
  | 'invite' | 'send' | 'archive' | 'restore'
  | 'other';

export interface AuditLogEntry {
  id: string;
  actor: string | null;
  actor_name: string;
  actor_email: string;
  action: AuditAction;
  action_label: string;
  entity_type: string;
  entity_id: string | null;
  entity_name: string;
  details: Record<string, unknown>;
  created_at: string;
}

// ── Onboarding Types (Phase 4) ──────────────────────────────────────────

export interface OnboardingStatus {
  is_onboarded: boolean;
  company_done: boolean;
  invite_done: boolean;
  import_done: boolean;
  email_done: boolean;
  pipeline_done: boolean;
  skipped_steps: string[];
  tenant: {
    name: string;
    logo_url: string;
    industry: string;
  };
}

export type PipelineTemplate = 'sales' | 'saas' | 'recruiting' | 'custom';

export interface OnboardingProgressPayload {
  company_done?: boolean;
  company?: {
    name?: string;
    logo_url?: string;
    industry?: string;
  };
  invite_done?: boolean;
  import_done?: boolean;
  email_done?: boolean;
  pipeline_done?: boolean;
  pipeline_template?: PipelineTemplate;
  mark_complete?: boolean;
  skip_step?: string;
}

export const PIPELINE_TEMPLATES: Record<PipelineTemplate, { name: string; stages: string[] }> = {
  sales: {
    name: 'Sales Pipeline',
    stages: ['Lead', 'Qualified', 'Proposal', 'Negotiation', 'Closed Won'],
  },
  saas: {
    name: 'SaaS Sales Pipeline',
    stages: ['Trial', 'Demo', 'Negotiation', 'Closed'],
  },
  recruiting: {
    name: 'Recruitment Pipeline',
    stages: ['Sourced', 'Screening', 'Interview', 'Offer', 'Hired'],
  },
  custom: {
    name: 'Custom Pipeline',
    stages: ['Lead', 'Qualified', 'Closed'],
  },
};

export const ONBOARDING_STEPS = [
  { key: 'company', label: 'Company', icon: 'Building2' },
  { key: 'invite', label: 'Invite', icon: 'UserPlus' },
  { key: 'import', label: 'Import', icon: 'Upload' },
  { key: 'email', label: 'Email', icon: 'Mail' },
  { key: 'pipeline', label: 'Pipeline', icon: 'GitBranch' },
] as const;

export interface TaskItem {
  id: string;
  title: string;
  description: string;
  priority: TaskPriority;
  status: TaskStatus2;
  due_at: string | null;
  completed_at: string | null;
  owner_id: string | null;
  assignee_id: string | null;
  entity_type: string;
  entity_id: string | null;
  tenant_id: string;
  created_at: string;
  updated_at: string;
}

export interface Team {
  id: string;
  name: string;
  description: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  is_admin: boolean;
  permissions: Record<string, boolean>;
  tenant_id: string;
  created_at: string;
  updated_at: string;
}

export interface Membership {
  id: string;
  user: string;
  user_email: string;
  user_name?: string;
  tenant: string;
  tenant_name: string;
  role: string;
  role_name: string;
  team: string | null;
  is_owner: boolean;
  joined_at: string;
}

export interface TimelineActor {
  id: string;
  name: string;
  avatar_url: string;
}

export interface TimelineEntity {
  type: string;
  id: string;
  name: string;
  url: string;
}

export interface TimelineEntry {
  id: string;
  activity_type: ActivityType;
  title: string;
  description: string;
  created_at: string;
  actor: TimelineActor;
  entity: TimelineEntity;
  metadata: Record<string, unknown>;
}

export interface TimelineResponse {
  count: number;
  page: number;
  page_size: number;
  total_pages: number;
  next: string | null;
  previous: string | null;
  results: TimelineEntry[];
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// ── Bulk Operations (Phase 4) ──────────────────────────────────────────

export type BulkOperation = 'delete' | 'assign' | 'change_stage' | 'change_status' | 'add_tag' | 'remove_tag' | 'replace_tags';

export type BulkJobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'partial';

export interface BulkPayload {
  record_ids?: string[];
  filter_params?: Record<string, string>;
  owner_id?: string;
  stage_id?: string;
  status?: string;
  close_reason?: string;
  tags?: string[];
}

export interface BulkJob {
  id: string;
  operation: BulkOperation;
  entity_type: string;
  status: BulkJobStatus;
  total_count: number;
  processed_count: number;
  success_count: number;
  error_count: number;
  errors: { id: string; reason: string }[];
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface BulkResponse {
  status: BulkJobStatus;
  bulk_job_id: string;
  total: number;
  success: number;
  errors: { id: string; reason: string }[];
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface SignupPayload {
  email: string;
  username: string;
  password: string;
  first_name: string;
  last_name: string;
  organization_name?: string;
}

export interface DashboardMetrics {
  total_pipeline_value: number;
  won_value: number;
  win_rate: number;
  active_deals: number;
  avg_deal_value: number;
  deals_by_stage: { stage_name: string; count: number; value: number }[];
  activities_this_week: number;
  tasks_due: number;
  recent_deals: Deal[];
}

// ── Report Types (ADR-007) ────────────────────────────────────────────

export interface DashboardReport {
  period: { start_date: string; end_date: string; label: string };
  summary: {
    total_pipeline_value: number;
    pipeline_value_change: number | null;
    won_value: number;
    won_value_change: number | null;
    lost_value: number;
    win_rate: number;
    win_rate_change: number | null;
    active_deals: number;
    active_deals_change: number | null;
    avg_deal_value: number;
    avg_deal_value_change: number | null;
    avg_days_to_close: number;
    weighted_pipeline: number;
  };
  pipeline_value_trend: { date: string; value: number }[];
  deals_by_stage: { stage_name: string; stage_id: string; count: number; value: number; probability: number }[];
  win_rate_by_stage: { from_stage: string; to_stage: string; conversion_rate: number; deals_entered: number; deals_converted: number }[];
  deal_velocity: { stage_name: string; avg_days: number; deals_in_stage: number }[];
  activity_metrics: {
    total: number;
    by_type: { activity_type: string; label: string; count: number }[];
    by_day: { date: string; count: number }[];
    calls_with_duration: { total_minutes: number; avg_minutes: number };
  };
  tasks_summary: {
    total_due: number;
    overdue: number;
    due_today: number;
    by_priority: Record<string, number>;
  };
  by_owner?: OwnerMetrics[];
}

export interface OwnerMetrics {
  owner_id: string;
  owner_name: string;
  pipeline_value: number;
  won_value: number;
  win_rate: number;
  active_deals: number;
  won_deals: number;
  lost_deals: number;
  avg_deal_value: number;
  activity_count: number;
}

export interface StaleDeal {
  id: string;
  name: string;
  value: number;
  stage_name: string;
  owner_name: string;
  days_in_stage: number;
  days_since_last_activity: number;
  expected_close_date: string | null;
  is_overdue: boolean;
}

export interface SimpleWeightedProjection {
  projected_revenue: number;
  deals_in_pipeline: number;
  total_pipeline_value: number;
  description: string;
}

export interface WinRateAdjustedProjection {
  projected_revenue: number;
  historical_win_rate: number;
  adjustment_factor: number;
  description: string;
}

export interface MonthlyBreakdown {
  month: string;
  projected_value: number;
  expected_deals: number;
}

export interface VelocityBasedProjection {
  projected_revenue: number;
  expected_close_count: number;
  deals_with_expected_dates: number;
  avg_days_to_close: number;
  monthly_breakdown: MonthlyBreakdown[];
}

export interface WhatIfScenario {
  stage_name: string;
  current_close_rate: number;
  scenario_close_rate: number;
  deals_affected: number;
  current_projected_value: number;
  scenario_projected_value: number;
  upside: number;
}

export interface DealForecast {
  deal_id: string;
  deal_name: string;
  deal_value: number;
  stage_name: string;
  stage_probability: number;
  probability_weight: number;
  projected_value: number;
  estimated_close_date: string | null;
  pipeline_name: string;
  has_expected_date: boolean;
}

export interface ForecastPeriod {
  quarter: string;
  start_date: string;
  end_date: string;
  label: string;
}

export interface ForecastScenario {
  stage_name: string;
  close_rate: number;
  confidence_level: string;
}

export interface ForecastResponse {
  period: ForecastPeriod;
  projections: {
    simple_weighted: SimpleWeightedProjection;
    win_rate_adjusted: WinRateAdjustedProjection;
    velocity_based: VelocityBasedProjection;
  };
  scenario: ForecastScenario | null;
  what_if: WhatIfScenario | null;
  deal_forecasts: DealForecast[];
}

export interface ForecastQueryParams {
  pipeline_id?: string;
  quarter?: string;
  range?: 'quarter' | 'half-year' | 'year';
  scenario_stage?: string;
  scenario_close_rate?: number;
  confidence_level?: 'conservative' | 'medium' | 'optimistic';
}

// ── Report types ───────────────────────────────────────────────

export interface DashboardReport {
  period: { start_date: string; end_date: string; label: string };
  summary: {
    total_pipeline_value: number;
    pipeline_value_change: number | null;
    won_value: number;
    won_value_change: number | null;
    lost_value: number;
    win_rate: number;
    win_rate_change: number | null;
    active_deals: number;
    active_deals_change: number | null;
    avg_deal_value: number;
    avg_deal_value_change: number | null;
    avg_days_to_close: number;
    weighted_pipeline: number;
  };
  pipeline_value_trend: { date: string; value: number }[];
  deals_by_stage: {
    stage_name: string;
    stage_id: string;
    count: number;
    value: number;
    probability: number;
  }[];
  win_rate_by_stage: {
    from_stage: string;
    to_stage: string;
    conversion_rate: number;
    deals_entered: number;
    deals_converted: number;
  }[];
  deal_velocity: {
    stage_name: string;
    avg_days: number;
    deals_in_stage: number;
  }[];
  activity_metrics: {
    total: number;
    by_type: { activity_type: string; label: string; count: number }[];
    by_day: { date: string; count: number }[];
    calls_with_duration: { total_minutes: number; avg_minutes: number };
  };
  tasks_summary: {
    total_due: number;
    overdue: number;
    due_today: number;
    by_priority: Record<string, number>;
  };
  by_owner?: OwnerMetrics[];
}

export interface OwnerMetrics {
  owner_id: string;
  owner_name: string;
  pipeline_value: number;
  won_value: number;
  win_rate: number;
  active_deals: number;
  won_deals: number;
  lost_deals: number;
  avg_deal_value: number;
  activity_count: number;
}

export interface StaleDeal {
  id: string;
  name: string;
  value: number;
  stage_name: string;
  owner_name: string;
  days_in_stage: number;
  days_since_last_activity: number;
  expected_close_date: string | null;
  is_overdue: boolean;
}

export interface StaleDealsResponse {
  stale_deals: StaleDeal[];
}

// ── API Keys ────────────────────────────────────────────────
export interface APIKey {
  id: string;
  name: string;
  key_prefix: string;
  permissions: Record<string, boolean>;
  expires_at: string | null;
  last_used_at: string | null;
  last_ip_address: string | null;
  is_active: boolean;
  revoked_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreatedAPIKey extends APIKey {
  key: string;  // plaintext key — shown only once at creation
}

// ── 2FA / TOTP Types ────────────────────────────────────────────────
export interface TwoFactorStatus {
  totp_enabled: boolean;
  tenant_requires_2fa: boolean;
  has_recovery_codes: boolean;
  remaining_recovery_codes: number;
}

export interface TwoFactorSetupResponse {
  secret: string;
  provisioning_uri: string;
}

export interface TwoFactorConfirmResponse {
  detail: string;
  recovery_codes: string[];
}

export interface TwoFactorLoginResponse {
  access: string;
  refresh: string;
  user: User;
  remaining_codes?: number;
}

export interface TwoFactorRequiredResponse {
  '2fa_required': boolean;
  '2fa_token': string;
  user: { id: string; email: string };
}

// ── SAML Types ───────────────────────────────────────────────────────
export interface SamlProvider {
  id: string;
  idp_entity_id: string;
  idp_sso_url: string;
  idp_slo_url: string;
  idp_x509_cert: string;
  attribute_mapping: Record<string, string>;
  default_role_id: string | null;
  auto_create_users: boolean;
  allowed_domains: string[];
  is_active: boolean;
  sp_entity_id: string;
  acs_url: string;
  last_used_at: string | null;
  tenant_id: string;
}

export interface SamlDomainCheckResponse {
  has_saml: boolean;
  provider_name?: string;
}

// ── Email Templates (Phase 5) ──────────────────────────────────────────
export interface EmailTemplate {
  id: string;
  tenant_id: string;
  name: string;
  description: string;
  subject_template: string;
  body_html: string;
  body_text: string;
  category: string;
  is_shared: boolean;
  created_by: { id: string; name: string } | null;
  created_by_name?: string | null;
  variables_used: string[];
  created_at: string;
  updated_at: string;
}

export interface TemplatePreview {
  rendered_subject: string;
  rendered_body_html: string;
  rendered_body_text: string;
  unresolved_variables: string[];
  entity_preview?: {
    contact?: { id: string; name: string; email: string };
    deal?: { id: string; name: string; value: string };
  };
}

