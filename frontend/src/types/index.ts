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

export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';
export type TaskStatus2 = 'todo' | 'in_progress' | 'done' | 'cancelled';

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
  tenant: string;
  tenant_name: string;
  role: string;
  role_name: string;
  team: string | null;
  is_owner: boolean;
  joined_at: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
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

export interface StaleDealsResponse {
  stale_deals: StaleDeal[];
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

