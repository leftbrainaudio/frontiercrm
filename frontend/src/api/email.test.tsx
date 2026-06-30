import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useEmails, useEmail, useSendEmail, useToggleStar, useMarkRead } from './email';
import type { EmailMessage } from '../types';

vi.mock('./client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
}));

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
  success: vi.fn(),
  error: vi.fn(),
}));

import apiClient from './client';
import toast from 'react-hot-toast';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('useEmails', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches email list', async () => {
    const mockData = { results: [{ id: 'e1' } as EmailMessage] };
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockData });

    const { result } = renderHook(() => useEmails(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(apiClient.get).toHaveBeenCalledWith('/emails/', { params: undefined });
    expect(result.current.data).toEqual(mockData);
  });

  it('passes params to API', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: { results: [] } });

    renderHook(() => useEmails({ direction: 'outbound' }), { wrapper: createWrapper() });

    await waitFor(() => expect(apiClient.get).toHaveBeenCalled());
    expect(apiClient.get).toHaveBeenCalledWith('/emails/', { params: { direction: 'outbound' } });
  });

  it('handles empty results', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: { results: [] } });

    const { result } = renderHook(() => useEmails(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual({ results: [] });
  });
});

describe('useEmail', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches single email by id', async () => {
    const mockEmail = { id: 'e1', subject: 'Test' } as EmailMessage;
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockEmail });

    const { result } = renderHook(() => useEmail('e1'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(apiClient.get).toHaveBeenCalledWith('/emails/e1/');
    expect(result.current.data).toEqual(mockEmail);
  });

  it('does not fetch when id is undefined', () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: {} });

    const { result } = renderHook(() => useEmail(undefined), { wrapper: createWrapper() });

    expect(result.current.isPending).toBe(true); // query is disabled
    expect(apiClient.get).not.toHaveBeenCalled();
  });
});

describe('useToggleStar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls toggle_star endpoint', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ data: {} });

    const { result } = renderHook(() => useToggleStar(), { wrapper: createWrapper() });

    await act(async () => {
      result.current.mutate('email-1');
    });

    expect(apiClient.post).toHaveBeenCalledWith('/emails/email-1/toggle_star/');
  });
});

describe('useMarkRead', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls mark_read endpoint', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ data: {} });

    const { result } = renderHook(() => useMarkRead(), { wrapper: createWrapper() });

    await act(async () => {
      result.current.mutate('email-1');
    });

    expect(apiClient.post).toHaveBeenCalledWith('/emails/email-1/mark_read/');
  });
});

describe('useSendEmail', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('creates email and polls until sent', async () => {
    // POST /emails/ returns created email with SENDING status
    vi.mocked(apiClient.post).mockResolvedValueOnce({
      data: { id: 'email-123', status: 'sending' } as EmailMessage,
    });
    // First poll returns still sending
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { status: 'sending' },
    });
    // Second poll returns sent
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { status: 'sent', message_id: 'gmail-abc' },
    });

    const { result } = renderHook(() => useSendEmail(), { wrapper: createWrapper() });

    let sendResult: { emailId: string; status: string; message_id?: string } | undefined;
    await act(async () => {
      sendResult = await result.current.mutateAsync({
        to_emails: ['test@example.com'],
        subject: 'Test',
        body_text: 'Hello',
      });
    });

    expect(vi.mocked(apiClient.post)).toHaveBeenCalledWith('/emails/', {
      to_emails: ['test@example.com'],
      subject: 'Test',
      body_text: 'Hello',
    });
    expect(sendResult).toMatchObject({
      emailId: 'email-123',
      status: 'sent',
      message_id: 'gmail-abc',
    });
    // Should have invalidated email queries
    expect(toast.success).toHaveBeenCalledWith('Email sent');
  });

  it('returns failed status when Gmail send fails', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({
      data: { id: 'email-456', status: 'sending' } as EmailMessage,
    });
    // Poll returns failed
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { status: 'failed', error_message: 'Gmail error' },
    });

    const { result } = renderHook(() => useSendEmail(), { wrapper: createWrapper() });

    let sendResult: { emailId: string; status: string } | undefined;
    await act(async () => {
      sendResult = await result.current.mutateAsync({
        to_emails: ['bad@example.com'],
        subject: 'Fail Test',
        body_text: 'Oops',
      });
    });

    expect(sendResult).toMatchObject({
      emailId: 'email-456',
      status: 'failed',
      error_message: 'Gmail error',
    });
    // No success toast on failure
    expect(toast.success).not.toHaveBeenCalled();
  });

  it('shows error toast on mutation error', async () => {
    vi.mocked(apiClient.post).mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useSendEmail(), { wrapper: createWrapper() });

    await act(async () => {
      try {
        await result.current.mutateAsync({
          to_emails: ['test@example.com'],
          subject: 'Test',
          body_text: 'Hello',
        });
      } catch {
        // expected
      }
    });

    expect(toast.error).toHaveBeenCalledWith('Failed to send email');
  });
});
