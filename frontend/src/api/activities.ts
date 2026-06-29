import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from './client';
import type { Activity, PaginatedResponse } from '../types';

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