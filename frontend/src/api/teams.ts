import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from './client';
import type { Team, Role, Membership } from '../types';

export function useTeams() {
  return useQuery({
    queryKey: ['teams'],
    queryFn: () => apiClient.get<{ results: Team[] }>('/teams/teams/').then((r) => r.data.results),
  });
}

export function useRoles() {
  return useQuery({
    queryKey: ['roles'],
    queryFn: () => apiClient.get<{ results: Role[] }>('/teams/roles/').then((r) => r.data.results),
  });
}

export function useUsers() {
  return useQuery({
    queryKey: ['memberships'],
    queryFn: () =>
      apiClient.get<{ results: Membership[] }>('/teams/memberships/').then((r) => r.data.results),
  });
}

export function useMemberships() {
  return useUsers();
}

export function useUpdateUserRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ membershipId, roleId }: { membershipId: string; roleId: string }) =>
      apiClient.patch(`/teams/memberships/${membershipId}/`, { role_id: roleId }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['memberships'] });
    },
  });
}

export function useInviteMember() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { email: string; role_id?: string }) =>
      apiClient.post('/teams/memberships/invite/', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['memberships'] }),
  });
}