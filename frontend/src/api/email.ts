import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from './client';
import type { EmailMessage, PaginatedResponse } from '../types';

export function useEmails(params?: Record<string, string>) {
  return useQuery({
    queryKey: ['emails', params],
    queryFn: () =>
      apiClient.get<PaginatedResponse<EmailMessage>>('/emails/', { params }).then((r) => r.data),
  });
}

export function useEmail(id: string | undefined) {
  return useQuery({
    queryKey: ['emails', id],
    queryFn: () => apiClient.get<EmailMessage>(`/emails/${id}/`).then((r) => r.data),
    enabled: !!id,
  });
}

export function useToggleStar() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.post(`/emails/${id}/toggle_star/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['emails'] }),
  });
}

export function useMarkRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.post(`/emails/${id}/mark_read/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['emails'] }),
  });
}

export function useSendEmail() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<EmailMessage>) => apiClient.post('/emails/', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['emails'] }),
  });
}