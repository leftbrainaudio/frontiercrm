import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from './client';
import type { CustomFieldDef } from '../types';

export function useCustomFieldDefs(entityType?: string) {
  const params = entityType ? { entity_type: entityType } : undefined;
  return useQuery({
    queryKey: ['custom-field-defs', params],
    queryFn: () =>
      apiClient.get<{ results: CustomFieldDef[] }>('/custom-fields/custom-fields/', {
        params,
      }).then((r) => r.data.results),
  });
}

export function useCreateCustomFieldDef() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<CustomFieldDef>) =>
      apiClient.post('/custom-fields/custom-fields/', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['custom-field-defs'] }),
  });
}

export function useUpdateCustomFieldDef() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: Partial<CustomFieldDef> & { id: string }) =>
      apiClient.patch(`/custom-fields/custom-fields/${id}/`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['custom-field-defs'] }),
  });
}

export function useDeleteCustomFieldDef() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/custom-fields/custom-fields/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['custom-field-defs'] }),
  });
}
