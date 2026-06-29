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