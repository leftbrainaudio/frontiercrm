import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from './client';
import type { Pipeline } from '../types';

export interface SlackWebhook {
  id: string;
  webhook_url: string;
  channel_override: string;
  display_name: string;
  subscribed_events: string[];
  pipeline_filter: { id: string; name: string } | null;
  is_active: boolean;
  last_triggered_at: string | null;
  failure_count: number;
  tenant_id: string;
  created_at: string;
  updated_at: string;
}

export interface SlackWebhookCreate {
  webhook_url: string;
  channel_override?: string;
  display_name?: string;
  subscribed_events?: string[];
  pipeline_filter_id?: string | null;
}

export interface SlackWebhookUpdate {
  webhook_url?: string;
  channel_override?: string;
  display_name?: string;
  subscribed_events?: string[];
  pipeline_filter_id?: string | null;
  is_active?: boolean;
}

const EVENT_LABELS: Record<string, string> = {
  deal_stage_change: 'Deal Stage Changes',
  deal_status_change: 'Deal Won/Lost',
  email: 'Emails',
  note: 'Notes',
  call: 'Calls',
  meeting: 'Meetings',
  task: 'Tasks',
  file_upload: 'File Uploads',
  system: 'System Events',
};

export function getEventLabel(key: string): string {
  return EVENT_LABELS[key] || key;
}

export const DEFAULT_SUBSCRIBED_EVENTS = [
  'deal_stage_change',
  'deal_status_change',
  'email',
];

export function useSlackWebhooks() {
  return useQuery({
    queryKey: ['slack-webhooks'],
    queryFn: () =>
      apiClient.get<SlackWebhook[]>('/slack/webhooks/').then((r) => r.data),
  });
}

export function useCreateSlackWebhook() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: SlackWebhookCreate) =>
      apiClient.post('/slack/webhooks/', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['slack-webhooks'] }),
  });
}

export function useUpdateSlackWebhook() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: SlackWebhookUpdate & { id: string }) =>
      apiClient.patch(`/slack/webhooks/${id}/`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['slack-webhooks'] }),
  });
}

export function useDeleteSlackWebhook() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/slack/webhooks/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['slack-webhooks'] }),
  });
}

export function useTestSlackWebhook() {
  return useMutation({
    mutationFn: (id: string) =>
      apiClient.post(`/slack/webhooks/${id}/test/`),
  });
}

export function useDeactivateSlackWebhook() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiClient.post(`/slack/webhooks/${id}/deactivate/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['slack-webhooks'] }),
  });
}

export function usePipelinesList() {
  return useQuery({
    queryKey: ['pipelines-list'],
    queryFn: () =>
      apiClient.get<{ results: Pipeline[] }>('/deals/pipelines/').then((r) => r.data.results),
  });
}