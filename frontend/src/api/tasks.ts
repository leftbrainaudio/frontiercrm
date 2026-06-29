import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from './client';
import type { TaskItem, PaginatedResponse } from '../types';

export function useTasks(params?: Record<string, string>) {
  return useQuery({
    queryKey: ['tasks', params],
    queryFn: () =>
      apiClient.get<PaginatedResponse<TaskItem>>('/tasks/', { params }).then((r) => r.data),
  });
}

export function useCreateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<TaskItem>) => apiClient.post('/tasks/', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tasks'] }),
  });
}

export function useUpdateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: Partial<TaskItem> & { id: string }) =>
      apiClient.patch(`/tasks/${id}/`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tasks'] }),
  });
}

export function useCompleteTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.post(`/tasks/${id}/complete/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tasks'] }),
  });
}