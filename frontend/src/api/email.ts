import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
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

export interface SendStatus {
  status: 'sending' | 'sent' | 'failed';
  error_message?: string;
  message_id?: string;
}

const POLL_INTERVAL = 2000;
const POLL_TIMEOUT = 30000;

async function pollSendStatus(emailId: string): Promise<SendStatus> {
  const start = Date.now();

  const poll = async (): Promise<SendStatus> => {
    if (Date.now() - start >= POLL_TIMEOUT) {
      return { status: 'failed', error_message: 'Send is taking longer than expected — check your sent folder later.' };
    }

    const { data } = await apiClient.get<SendStatus>(`/emails/${emailId}/send_status/`);

    if (data.status === 'sent' || data.status === 'failed') {
      return data;
    }

    // Wait 2s before next poll
    await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL));
    return poll();
  };

  return poll();
}

export function useSendEmail() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<EmailMessage>): Promise<{ emailId: string } & SendStatus> => {
      // POST to create the email in SENDING state
      const { data: created } = await apiClient.post<EmailMessage>('/emails/', data);
      const emailId = created.id;

      // Poll for completion
      const sendResult = await pollSendStatus(emailId);

      return { emailId, ...sendResult };
    },
    onSuccess: (result) => {
      qc.invalidateQueries({ queryKey: ['emails'] });
      if (result.status === 'sent') {
        toast.success('Email sent');
      }
    },
    onError: () => {
      toast.error('Failed to send email');
    },
  });
}