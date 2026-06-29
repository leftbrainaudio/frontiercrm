import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from './client';
import type { Contact, Account, PaginatedResponse } from '../types';

// ── Contacts ──

export function useContacts(params?: Record<string, string>) {
  return useQuery({
    queryKey: ['contacts', params],
    queryFn: () =>
      apiClient.get<PaginatedResponse<Contact>>('/contacts/contacts/', { params }).then((r) => r.data),
  });
}

export function useContact(id: string | undefined) {
  return useQuery({
    queryKey: ['contacts', id],
    queryFn: () => apiClient.get<Contact>(`/contacts/contacts/${id}/`).then((r) => r.data),
    enabled: !!id,
  });
}

export function useCreateContact() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Contact>) => apiClient.post('/contacts/contacts/', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['contacts'] }),
  });
}

export function useUpdateContact() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: Partial<Contact> & { id: string }) =>
      apiClient.patch(`/contacts/contacts/${id}/`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['contacts'] }),
  });
}

export function useDeleteContact() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/contacts/contacts/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['contacts'] }),
  });
}

// ── Accounts ──

export function useAccounts(params?: Record<string, string>) {
  return useQuery({
    queryKey: ['accounts', params],
    queryFn: () =>
      apiClient.get<PaginatedResponse<Account>>('/contacts/accounts/', { params }).then((r) => r.data),
  });
}

export function useAccount(id: string | undefined) {
  return useQuery({
    queryKey: ['accounts', id],
    queryFn: () => apiClient.get<Account>(`/contacts/accounts/${id}/`).then((r) => r.data),
    enabled: !!id,
  });
}

export function useCreateAccount() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Account>) => apiClient.post('/contacts/accounts/', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['accounts'] }),
  });
}

export function useUpdateAccount() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: Partial<Account> & { id: string }) =>
      apiClient.patch(`/contacts/accounts/${id}/`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['accounts'] }),
  });
}

export function useDeleteAccount() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/contacts/accounts/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['accounts'] }),
  });
}