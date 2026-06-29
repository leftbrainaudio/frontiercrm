import { useQuery } from '@tanstack/react-query';
import apiClient from './client';
import type { DashboardReport, StaleDealsResponse } from '../types';

export function useDashboardReport(params?: Record<string, string>) {
  return useQuery({
    queryKey: ['reports', 'dashboard', params],
    queryFn: () =>
      apiClient.get<DashboardReport>('/reports/dashboard/', { params }).then((r) => r.data),
  });
}

export function useStaleDeals(params?: Record<string, string>) {
  return useQuery({
    queryKey: ['reports', 'stale-deals', params],
    queryFn: () =>
      apiClient.get<StaleDealsResponse>('/reports/stale-deals/', { params }).then((r) => r.data),
  });
}