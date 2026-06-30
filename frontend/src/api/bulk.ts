import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from './client';
import type { BulkPayload, BulkJob, BulkResponse } from '../types';

// ── Helper ──

function getBulkUrl(entity: string, operation: string): string {
  if (entity === 'account') {
    return `/contacts/bulk/accounts/${operation}/`;
  }
  return `/${entity === 'deal' ? 'deals' : 'contacts'}/bulk/${operation}/`;
}

// ── Bulk Operation Mutations ──

export function useBulkDelete(entity: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: BulkPayload) =>
      apiClient.post<BulkResponse>(getBulkUrl(entity, 'delete/'), payload),
    onSuccess: (res) => {
      if (res.data.status === 'completed') {
        qc.invalidateQueries({ queryKey: [entity === 'account' ? 'accounts' : `${entity}s`] });
      }
    },
  });
}

export function useBulkAssign(entity: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: BulkPayload) =>
      apiClient.post<BulkResponse>(getBulkUrl(entity, 'assign/'), payload),
    onSuccess: (res) => {
      if (res.data.status === 'completed') {
        qc.invalidateQueries({ queryKey: [`${entity}s`] });
      }
    },
  });
}

export function useBulkChangeStage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: BulkPayload) =>
      apiClient.post<BulkResponse>('/deals/bulk/change-stage/', payload),
    onSuccess: (res) => {
      if (res.data.status === 'completed') {
        qc.invalidateQueries({ queryKey: ['deals'] });
      }
    },
  });
}

export function useBulkChangeStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: BulkPayload) =>
      apiClient.post<BulkResponse>('/deals/bulk/change-status/', payload),
    onSuccess: (res) => {
      if (res.data.status === 'completed') {
        qc.invalidateQueries({ queryKey: ['deals'] });
      }
    },
  });
}

export function useBulkAddTag(entity: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: BulkPayload) =>
      apiClient.post<BulkResponse>(getBulkUrl(entity, 'tags/add/'), payload),
    onSuccess: (res) => {
      if (res.data.status === 'completed') {
        qc.invalidateQueries({ queryKey: [`${entity === 'account' ? 'accounts' : `${entity}s`}`] });
      }
    },
  });
}

export function useBulkRemoveTag(entity: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: BulkPayload) =>
      apiClient.post<BulkResponse>(getBulkUrl(entity, 'tags/remove/'), payload),
    onSuccess: (res) => {
      if (res.data.status === 'completed') {
        qc.invalidateQueries({ queryKey: [`${entity === 'account' ? 'accounts' : `${entity}s`}`] });
      }
    },
  });
}

export function useBulkReplaceTags(entity: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: BulkPayload) =>
      apiClient.post<BulkResponse>(getBulkUrl(entity, 'tags/replace/'), payload),
    onSuccess: (res) => {
      if (res.data.status === 'completed') {
        qc.invalidateQueries({ queryKey: [`${entity === 'account' ? 'accounts' : `${entity}s`}`] });
      }
    },
  });
}

// ── Bulk Job Polling ──

export function useBulkJob(jobId: string | null) {
  return useQuery({
    queryKey: ['bulk-job', jobId],
    queryFn: () =>
      apiClient.get<BulkJob>(`/core/bulk-jobs/${jobId}/`).then((r) => r.data),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 2000;
      if (data.status === 'completed' || data.status === 'failed' || data.status === 'partial') {
        return false;
      }
      const elapsed = Date.now() - new Date(data.started_at ?? data.created_at).getTime();
      return elapsed > 30000 ? 5000 : 2000;
    },
  });
}

export function useCancelBulkJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) =>
      apiClient.post(`/core/bulk-jobs/${jobId}/cancel/`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['bulk-job'] });
    },
  });
}

// ── Bulk Export ──

export function useBulkExportUrl(
  entity: string,
  params: Record<string, string>,
  selectedIds?: string[],
) {
  const searchParams = new URLSearchParams(params);
  if (selectedIds?.length) {
    searchParams.set('record_ids', selectedIds.join(','));
  }
  const basePath = entity === 'account'
    ? '/contacts/bulk/accounts/export/csv/'
    : `/${entity === 'deal' ? 'deals' : 'contacts'}/bulk/export/csv/`;
  return {
    url: `${basePath}?${searchParams.toString()}`,
    filename: `${entity}s.csv`,
  };
}
