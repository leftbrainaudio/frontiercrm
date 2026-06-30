import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from './client';
import type { Activity, PaginatedResponse, TimelineResponse } from '../types';

export function useActivities(params?: Record<string, string>) {
  return useQuery({
    queryKey: ['activities', params],
    queryFn: () =>
      apiClient.get<PaginatedResponse<Activity>>('/activities/', { params }).then((r) => r.data),
  });
}

export function useCreateActivity() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Activity>) => apiClient.post('/activities/', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['activities'] }),
  });
}

// ── Activity Timeline ────────────────────────────────────────────────

export interface TimelineParams {
  start_date?: string;
  end_date?: string;
  activity_type?: string;
  actor_id?: string;
  page?: number;
  page_size?: number;
}

export function useActivityTimeline(params?: TimelineParams) {
  return useQuery({
    queryKey: ['activity-timeline', params],
    queryFn: () =>
      apiClient
        .get<TimelineResponse>('/activities/timeline/', { params })
        .then((r) => r.data),
  });
}

export function useTimelineNextPage() {
  const qc = useQueryClient();
  return (params?: TimelineParams) => {
    qc.fetchQuery({
      queryKey: ['activity-timeline', params],
      queryFn: () =>
        apiClient
          .get<TimelineResponse>('/activities/timeline/', { params })
          .then((r) => r.data),
    });
  };
}
