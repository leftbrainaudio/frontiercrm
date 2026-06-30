import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from './client';
import type { EmailTemplate, PaginatedResponse, TemplatePreview } from '../types';

export function useEmailTemplates(params?: Record<string, string>) {
  return useQuery({
    queryKey: ['email-templates', params],
    queryFn: () =>
      apiClient
        .get<PaginatedResponse<EmailTemplate>>('/email-templates/', { params })
        .then((r) => r.data),
  });
}

export function useEmailTemplate(id: string | undefined) {
  return useQuery({
    queryKey: ['email-templates', id],
    queryFn: () =>
      apiClient.get<EmailTemplate>(`/email-templates/${id}/`).then((r) => r.data),
    enabled: !!id,
  });
}

export function useSaveTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<EmailTemplate> & { id?: string }) => {
      if (data.id) {
        return apiClient.patch(`/email-templates/${data.id}/`, data).then((r) => r.data);
      }
      return apiClient.post('/email-templates/', data).then((r) => r.data);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['email-templates'] }),
  });
}

export function useDeleteTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/email-templates/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['email-templates'] }),
  });
}

export function usePreviewTemplate() {
  return useMutation({
    mutationFn: ({
      id,
      context,
    }: {
      id: string;
      context: {
        contact_id?: string;
        deal_id?: string;
        account_id?: string;
        custom_variables?: Record<string, string>;
      };
    }) => apiClient.post<TemplatePreview>(`/email-templates/${id}/preview/`, { context }).then((r) => r.data),
  });
}

export function useTemplateVariables() {
  return useQuery({
    queryKey: ['email-template-variables'],
    queryFn: () =>
      apiClient
        .get<{ variables: Record<string, Array<{ name: string; label: string; source: string }>> }>(
          '/email-templates/variables/',
        )
        .then((r) => r.data),
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
}
