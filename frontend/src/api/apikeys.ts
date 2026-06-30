import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from './client';
import type { APIKey, CreatedAPIKey } from '../types';

export function useAPIKeys() {
  return useQuery({
    queryKey: ['api-keys'],
    queryFn: () =>
      apiClient.get<{ results: APIKey[] }>('/api-keys/')
        .then((r) => r.data.results),
  });
}

export function useCreateAPIKey() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; permissions?: Record<string, boolean>; expires_at?: string }) =>
      apiClient.post<CreatedAPIKey>('/api-keys/', data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['api-keys'] });
    },
  });
}

export function useRevokeAPIKey() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiClient.post(`/api-keys/${id}/revoke/`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['api-keys'] });
    },
  });
}

export function useDeleteAPIKey() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiClient.delete(`/api-keys/${id}/`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['api-keys'] });
    },
  });
}

export function useUpdateAPIKey() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: { id: string; name?: string; permissions?: Record<string, boolean>; expires_at?: string | null }) =>
      apiClient.patch<APIKey>(`/api-keys/${id}/`, data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['api-keys'] });
    },
  });
}
