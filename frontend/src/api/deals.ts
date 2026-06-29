import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from './client';
import type { Pipeline, Deal, PaginatedResponse } from '../types';

export function usePipelines() {
  return useQuery({
    queryKey: ['pipelines'],
    queryFn: () => apiClient.get<{ results: Pipeline[] }>('/deals/pipelines/').then((r) => r.data.results),
  });
}

export function usePipeline(id: string | undefined) {
  return useQuery({
    queryKey: ['pipelines', id],
    queryFn: () => apiClient.get<Pipeline>(`/deals/pipelines/${id}/`).then((r) => r.data),
    enabled: !!id,
  });
}

export function useDeals(params?: Record<string, string>) {
  return useQuery({
    queryKey: ['deals', params],
    queryFn: () =>
      apiClient.get<PaginatedResponse<Deal>>('/deals/deals/', { params }).then((r) => r.data),
  });
}

export function useDeal(id: string | undefined) {
  return useQuery({
    queryKey: ['deals', id],
    queryFn: () => apiClient.get<Deal>(`/deals/deals/${id}/`).then((r) => r.data),
    enabled: !!id,
  });
}

export function useCreateDeal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Deal>) => apiClient.post('/deals/deals/', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['deals'] }),
  });
}

export function useUpdateDeal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: Partial<Deal> & { id: string }) =>
      apiClient.patch(`/deals/deals/${id}/`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['deals'] }),
  });
}

export function useMoveDealStage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, stage_id }: { id: string; stage_id: string }) =>
      apiClient.post(`/deals/deals/${id}/move_stage/`, { stage_id }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['deals'] }),
  });
}

export function useChangeDealStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status, close_reason }: { id: string; status: string; close_reason?: string }) =>
      apiClient.post(`/deals/deals/${id}/change_status/`, { status, close_reason }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['deals'] }),
  });
}