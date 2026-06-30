import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from './client';
import type { SyncConnection, SyncState, CalendarAuthStatus, CalendarEventResponse, CalendarWatchStatus, ScopeUpgradeResponse } from '../types';

export function useSyncConnections(provider?: string) {
  const params: Record<string, string> = {};
  if (provider) params.provider = provider;

  return useQuery({
    queryKey: ['sync-connections', params],
    queryFn: () =>
      apiClient.get<SyncConnection[]>('/sync/connections/', { params }).then((r) => r.data),
  });
}

export function useGmailAuthUrl() {
  return useMutation({
    mutationFn: () =>
      apiClient.post<{ url: string; state: string }>('/sync/connections/gmail/auth-url/').then((r) => r.data),
  });
}

export function useGmailCallback() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ code, state }: { code: string; state: string }) =>
      apiClient.post<SyncConnection>('/sync/connections/gmail/callback/', { code, state }).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['sync-connections'] });
      qc.invalidateQueries({ queryKey: ['emails'] });
    },
  });
}

export function useTriggerSync() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (connectionId: string) =>
      apiClient.post(`/sync/connections/${connectionId}/sync/`).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['sync-states'] });
    },
  });
}

export function useDisconnectConnection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (connectionId: string) =>
      apiClient.post(`/sync/connections/${connectionId}/disconnect/`).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['sync-connections'] });
      qc.invalidateQueries({ queryKey: ['emails'] });
    },
  });
}

export function useSyncStates(connectionId?: string) {
  const params: Record<string, string> = {};
  if (connectionId) params.connection = connectionId;

  return useQuery({
    queryKey: ['sync-states', params],
    queryFn: () =>
      apiClient.get<SyncState[]>('/sync/states/', { params }).then((r) => r.data),
  });
}

// ── Calendar OAuth ─────────────────────────────────────────────────────────

export function useCalendarAuthUrl() {
  return useMutation({
    mutationFn: () =>
      apiClient
        .post<{ url: string; state: string }>('/sync/connections/calendar/auth-url/')
        .then((r) => r.data),
  });
}

export function useCalendarCallback() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ code, state }: { code: string; state: string }) =>
      apiClient
        .post<SyncConnection>('/sync/connections/calendar/callback/', { code, state })
        .then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['sync-connections'] });
      qc.invalidateQueries({ queryKey: ['calendar-auth-status'] });
    },
  });
}

export function useCalendarAuthStatus() {
  return useQuery({
    queryKey: ['calendar-auth-status'],
    queryFn: () =>
      apiClient
        .get<CalendarAuthStatus>('/sync/connections/calendar/auth-status/')
        .then((r) => r.data),
    refetchInterval: 30_000, // Poll every 30s to catch sync progress changes
  });
}

// ── Calendar Event CRUD ───────────────────────────────────────────────────

export function useCreateCalendarEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: any) =>
      apiClient
        .post<CalendarEventResponse>('/sync/connections/calendar/events/', data)
        .then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['activities'] });
      qc.invalidateQueries({ queryKey: ['activity-timeline'] });
    },
  });
}

export function useUpdateCalendarEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ activityId, data }: { activityId: string; data: any }) =>
      apiClient
        .put<CalendarEventResponse>(`/sync/connections/calendar/events/${activityId}/`, data)
        .then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['activities'] });
      qc.invalidateQueries({ queryKey: ['activity-timeline'] });
    },
  });
}

export function useDeleteCalendarEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (activityId: string) =>
      apiClient.delete(`/sync/connections/calendar/events/${activityId}/`).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['activities'] });
      qc.invalidateQueries({ queryKey: ['activity-timeline'] });
    },
  });
}

// ── Calendar Watch Status ────────────────────────────────────────────────

export function useCalendarWatchStatus() {
  return useQuery({
    queryKey: ['calendar-watch-status'],
    queryFn: () =>
      apiClient
        .get<CalendarWatchStatus>('/sync/connections/calendar/watch-status/')
        .then((r) => r.data),
    refetchInterval: 60_000,
  });
}

// ── Calendar Scope Upgrade ──────────────────────────────────────────────

export function useUpgradeCalendarScope() {
  return useMutation({
    mutationFn: (connectionId: string) =>
      apiClient
        .post<ScopeUpgradeResponse>(`/sync/connections/${connectionId}/calendar/upgrade-scope/`)
        .then((r) => r.data),
  });
}