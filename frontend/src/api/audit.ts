import { useQuery } from '@tanstack/react-query';
import apiClient from './client';
import type { AuditLogEntry, PaginatedResponse } from '../types';

export interface AuditLogFilters {
  entity_type?: string;
  actor_id?: string;
  action?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export function useAuditLog(filters: AuditLogFilters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== '') {
      params.set(key, String(value));
    }
  });

  const qs = params.toString();

  return useQuery({
    queryKey: ['audit-log', filters],
    queryFn: () =>
      apiClient
        .get<PaginatedResponse<AuditLogEntry>>(`/audit/${qs ? `?${qs}` : ''}`)
        .then((r) => r.data),
  });
}
