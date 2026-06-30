import { useQuery } from '@tanstack/react-query';
import apiClient from './client';
import type { EmailMessage, PaginatedResponse } from '../types';

export function useEmails(params?: Record<string, string>) {
  return useQuery({
    queryKey: ['emails', params],
    queryFn: () =>
      apiClient
        .get<PaginatedResponse<EmailMessage>>('/emails/', { params })
        .then((r) => r.data),
  });
}