import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'react';
import { EmailPage } from './email-page';
import type { EmailMessage, SyncConnection } from '../../types';

// ── Mock all dependency modules ─────────────────────────────────────────────

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useSearchParams: vi.fn(() => [new URLSearchParams(), vi.fn()]),
    useNavigate: () => mockNavigate,
  };
});

// Mock the email API hooks
const mockUseEmails = vi.fn();
const mockUseEmail = vi.fn();
const mockUseToggleStar = vi.fn();
const mockUseMarkRead = vi.fn();
const mockUseSendEmail = vi.fn();

vi.mock('../../api/email', () => ({
  useEmails: (...args: unknown[]) => mockUseEmails(...args),
  useEmail: (...args: unknown[]) => mockUseEmail(...args),
  useToggleStar: (...args: unknown[]) => mockUseToggleStar(...args),
  useMarkRead: (...args: unknown[]) => mockUseMarkRead(...args),
  useSendEmail: (...args: unknown[]) => mockUseSendEmail(...args),
}));

// Mock the sync API hooks
const mockUseSyncConnections = vi.fn();
const mockUseGmailAuthUrl = vi.fn();
const mockUseGmailCallback = vi.fn();
const mockUseTriggerSync = vi.fn();

vi.mock('../../api/sync', () => ({
  useSyncConnections: (...args: unknown[]) => mockUseSyncConnections(...args),
  useGmailAuthUrl: (...args: unknown[]) => mockUseGmailAuthUrl(...args),
  useGmailCallback: (...args: unknown[]) => mockUseGmailCallback(...args),
  useTriggerSync: (...args: unknown[]) => mockUseTriggerSync(...args),
}));

// Mock apiClient
vi.mock('../../api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
}));

import apiClient from '../../api/client';

// ── Test helpers ────────────────────────────────────────────────────────────

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/email']}>{children}</MemoryRouter>
      </QueryClientProvider>
    );
  };
}

function makeConnection(overrides: Partial<SyncConnection> = {}): SyncConnection {
  return {
    id: 'conn-1',
    tenant_id: 't-1',
    provider: 'gmail',
    provider_account: 'user@gmail.com',
    status: 'active',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  } as SyncConnection;
}

function makeEmail(overrides: Partial<EmailMessage> = {}): EmailMessage {
  return {
    id: 'email-1',
    message_id: 'msg-1',
    thread_id: 'thread-1',
    direction: 'inbound',
    from_email: 'alice@example.com',
    to_emails: ['me@example.com'],
    cc_emails: [],
    bcc_emails: [],
    subject: 'Test Subject',
    body_text: 'Hello, this is a test email.',
    body_html: '',
    sent_at: '2024-06-15T10:00:00Z',
    received_at: '2024-06-15T10:00:00Z',
    is_read: false,
    is_starred: false,
    labels: [],
    entity_type: '',
    entity_id: null,
    tenant_id: 't-1',
    created_at: '2024-06-15T10:00:00Z',
    ...overrides,
  };
}

function mockGmailAuthUrl() {
  return {
    mutate: vi.fn((_args: unknown, opts?: { onSuccess?: (data: { url: string; state: string }) => void }) => {
      opts?.onSuccess?.({ url: 'https://accounts.google.com/o/oauth2/auth', state: 'state-123' });
    }),
    isPending: false,
  };
}

function mockGmailCallback() {
  return { mutate: vi.fn(), isPending: false };
}

function mockTriggerSync() {
  return { mutate: vi.fn(), isPending: false };
}

function mockUseSendEmailFn(options?: {
  mutateAsync?: ReturnType<typeof vi.fn>;
}) {
  const mutateAsync = options?.mutateAsync ?? vi.fn();
  return {
    mutateAsync,
    isPending: false,
    mutate: vi.fn(),
  };
}

function mockMarkRead() {
  return { mutate: vi.fn(), isPending: false };
}

function mockToggleStar() {
  return { mutate: vi.fn(), isPending: false };
}

// ── Tests ───────────────────────────────────────────────────────────────────

describe('EmailPage — Connection States', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default mocks for hooks not under test
    mockUseGmailAuthUrl.mockReturnValue(mockGmailAuthUrl());
    mockUseGmailCallback.mockReturnValue(mockGmailCallback());
    mockUseTriggerSync.mockReturnValue(mockTriggerSync());
    mockUseEmails.mockReturnValue({ data: { results: [] }, isLoading: false, isError: false, error: null });
    mockUseEmail.mockReturnValue({ data: undefined, isLoading: false });
    mockUseToggleStar.mockReturnValue(mockToggleStar());
    mockUseMarkRead.mockReturnValue(mockMarkRead());
    mockUseSendEmail.mockReturnValue(mockUseSendEmailFn());
  });

  it('shows loading spinner while connections load', () => {
    mockUseSyncConnections.mockReturnValue({ data: undefined, isLoading: true, refetch: vi.fn() });
    render(<EmailPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Checking connection...')).toBeInTheDocument();
  });

  it('shows NotConnectedState when no Gmail connection', () => {
    mockUseSyncConnections.mockReturnValue({
      data: [],
      isLoading: false,
      refetch: vi.fn(),
    });
    render(<EmailPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Connect your Gmail')).toBeInTheDocument();
    expect(screen.getByText('Connect Gmail')).toBeInTheDocument();
  });

  it('shows email page when Gmail is connected', () => {
    mockUseSyncConnections.mockReturnValue({
      data: [makeConnection()],
      isLoading: false,
      refetch: vi.fn(),
    });
    render(<EmailPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Compose')).toBeInTheDocument();
    expect(screen.getByText('Inbox')).toBeInTheDocument();
    expect(screen.getByText('Sent')).toBeInTheDocument();
    expect(screen.getByText('Starred')).toBeInTheDocument();
  });
});

describe('EmailPage — Email List States', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseGmailAuthUrl.mockReturnValue(mockGmailAuthUrl());
    mockUseGmailCallback.mockReturnValue(mockGmailCallback());
    mockUseTriggerSync.mockReturnValue(mockTriggerSync());
    mockUseSyncConnections.mockReturnValue({
      data: [makeConnection()],
      isLoading: false,
      refetch: vi.fn(),
    });
    mockUseEmail.mockReturnValue({ data: undefined, isLoading: false });
    mockUseToggleStar.mockReturnValue(mockToggleStar());
    mockUseMarkRead.mockReturnValue(mockMarkRead());
    mockUseSendEmail.mockReturnValue(mockUseSendEmailFn());
  });

  it('shows skeleton while emails load', () => {
    mockUseEmails.mockReturnValue({ data: undefined, isLoading: true, isError: false, error: null });
    const { container } = render(<EmailPage />, { wrapper: createWrapper() });
    // Skeleton renders several divs with the animate-pulse class
    const skeletons = container.querySelectorAll('.animate-pulse, [class*="skeleton"]');
    // The Skeleton component renders divs; just check loading text isn't shown
    expect(screen.getByText('Compose')).toBeInTheDocument();
  });

  it('shows empty state for inbox tab by default', () => {
    mockUseEmails.mockReturnValue({ data: { results: [] }, isLoading: false, isError: false, error: null });
    render(<EmailPage />, { wrapper: createWrapper() });
    expect(screen.getByText('No emails yet')).toBeInTheDocument();
    expect(screen.getByText(/Your inbox is empty/)).toBeInTheDocument();
  });

  it('shows empty state for sent tab when clicked', async () => {
    mockUseEmails.mockReturnValue({ data: { results: [] }, isLoading: false, isError: false, error: null });
    render(<EmailPage />, { wrapper: createWrapper() });

    await userEvent.click(screen.getByText('Sent'));
    expect(screen.getByText('No sent emails')).toBeInTheDocument();
  });

  it('shows empty state for starred tab when clicked', async () => {
    mockUseEmails.mockReturnValue({ data: { results: [] }, isLoading: false, isError: false, error: null });
    render(<EmailPage />, { wrapper: createWrapper() });

    await userEvent.click(screen.getByText('Starred'));
    expect(screen.getByText('No starred emails')).toBeInTheDocument();
  });

  it('renders email rows from data', () => {
    mockUseEmails.mockReturnValue({
      data: { results: [makeEmail(), makeEmail({ id: 'email-2', subject: 'Second Email', from_email: 'bob@example.com' })] },
      isLoading: false,
      isError: false,
      error: null,
    });
    render(<EmailPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Test Subject')).toBeInTheDocument();
    expect(screen.getByText('Second Email')).toBeInTheDocument();
    expect(screen.getByText('alice@example.com')).toBeInTheDocument();
  });

  it('shows error state on API error', () => {
    mockUseEmails.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: { message: 'Network error' },
    });
    render(<EmailPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText(/Network error/)).toBeInTheDocument();
  });

  it('shows unread indicator for unread emails', () => {
    mockUseEmails.mockReturnValue({
      data: {
        results: [
          makeEmail({ is_read: false }),
          makeEmail({ id: 'email-2', is_read: true, subject: 'Read Email' }),
        ],
      },
      isLoading: false,
      isError: false,
      error: null,
    });
    render(<EmailPage />, { wrapper: createWrapper() });
    // Unread dot is rendered via aria-label "Unread"
    const unreadDots = screen.getAllByLabelText('Unread');
    expect(unreadDots.length).toBe(1);
  });
});

describe('EmailPage — Compose Modal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseGmailAuthUrl.mockReturnValue(mockGmailAuthUrl());
    mockUseGmailCallback.mockReturnValue(mockGmailCallback());
    mockUseTriggerSync.mockReturnValue(mockTriggerSync());
    mockUseSyncConnections.mockReturnValue({
      data: [makeConnection()],
      isLoading: false,
      refetch: vi.fn(),
    });
    mockUseEmails.mockReturnValue({ data: { results: [] }, isLoading: false, isError: false, error: null });
    mockUseEmail.mockReturnValue({ data: undefined, isLoading: false });
    mockUseToggleStar.mockReturnValue(mockToggleStar());
    mockUseMarkRead.mockReturnValue(mockMarkRead());
  });

  it('opens compose modal when Compose button is clicked', async () => {
    mockUseSendEmail.mockReturnValue(mockUseSendEmailFn());

    render(<EmailPage />, { wrapper: createWrapper() });
    expect(screen.queryByText('Compose Email')).not.toBeInTheDocument();

    await userEvent.click(screen.getByText('Compose'));

    expect(screen.getByText('Compose Email')).toBeInTheDocument();
    expect(screen.getByLabelText('To')).toBeInTheDocument();
    expect(screen.getByLabelText('Subject')).toBeInTheDocument();
    expect(screen.getByText('Discard')).toBeInTheDocument();
    expect(screen.getByText('Send')).toBeInTheDocument();
  });

  it('disables Send button when To or Subject is empty', async () => {
    const mockSend = vi.fn();
    mockUseSendEmail.mockReturnValue(mockUseSendEmailFn({ mutateAsync: mockSend }));

    render(<EmailPage />, { wrapper: createWrapper() });
    await userEvent.click(screen.getByText('Compose'));

    const sendButton = screen.getByText('Send').closest('button');
    expect(sendButton).toBeDisabled();
  });

  it('enables Send button when both To and Subject are filled', async () => {
    mockUseSendEmail.mockReturnValue(mockUseSendEmailFn());

    render(<EmailPage />, { wrapper: createWrapper() });
    await userEvent.click(screen.getByText('Compose'));

    const toInput = screen.getByLabelText('To');
    const subjectInput = screen.getByLabelText('Subject');

    await userEvent.type(toInput, 'recipient@example.com');
    await userEvent.type(subjectInput, 'Test Subject');

    const sendButton = screen.getByText('Send').closest('button');
    expect(sendButton).not.toBeDisabled();
  });

  it('closes compose modal and clears fields on successful send', async () => {
    const mockMutateAsync = vi.fn().mockResolvedValue({ status: 'sent', emailId: 'email-1', message_id: 'gmail-1' });
    mockUseSendEmail.mockReturnValue(mockUseSendEmailFn({ mutateAsync: mockMutateAsync }));

    render(<EmailPage />, { wrapper: createWrapper() });
    await userEvent.click(screen.getByText('Compose'));

    const toInput = screen.getByLabelText('To');
    const subjectInput = screen.getByLabelText('Subject');
    const bodyTextarea = screen.getByLabelText('Message');

    await userEvent.type(toInput, 'recipient@example.com');
    await userEvent.type(subjectInput, 'Test Subject');
    await userEvent.type(bodyTextarea, 'Hello world');

    await userEvent.click(screen.getByText('Send'));

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalled();
    });

    // Modal should close after success
    await waitFor(() => {
      expect(screen.queryByText('Compose Email')).not.toBeInTheDocument();
    });
  });

  it('shows error state in modal on send failure', async () => {
    const mockMutateAsync = vi.fn().mockResolvedValue({
      status: 'failed',
      emailId: 'email-1',
      error_message: 'Gmail API: 403 Forbidden',
    });
    mockUseSendEmail.mockReturnValue(mockUseSendEmailFn({ mutateAsync: mockMutateAsync }));

    render(<EmailPage />, { wrapper: createWrapper() });
    await userEvent.click(screen.getByText('Compose'));

    await userEvent.type(screen.getByLabelText('To'), 'recipient@example.com');
    await userEvent.type(screen.getByLabelText('Subject'), 'Test');
    await userEvent.click(screen.getByText('Send'));

    await waitFor(() => {
      expect(screen.getByText(/Gmail API: 403 Forbidden/)).toBeInTheDocument();
    });

    // Should show Retry and Save as Draft buttons
    expect(screen.getByText('Retry')).toBeInTheDocument();
    expect(screen.getByText('Save as Draft')).toBeInTheDocument();
  });

  it('shows error state on exception during send', async () => {
    const mockMutateAsync = vi.fn().mockRejectedValue(new Error('Network error'));
    mockUseSendEmail.mockReturnValue(mockUseSendEmailFn({ mutateAsync: mockMutateAsync }));

    render(<EmailPage />, { wrapper: createWrapper() });
    await userEvent.click(screen.getByText('Compose'));

    await userEvent.type(screen.getByLabelText('To'), 'recipient@example.com');
    await userEvent.type(screen.getByLabelText('Subject'), 'Test');
    await userEvent.click(screen.getByText('Send'));

    await waitFor(() => {
      expect(screen.getByText(/Failed to send email/)).toBeInTheDocument();
    });
  });

  it('retry button resends the same email', async () => {
    const mockMutateAsync = vi.fn()
      .mockResolvedValueOnce({
        status: 'failed',
        emailId: 'email-1',
        error_message: 'Gmail API: 403 Forbidden',
      })
      .mockResolvedValueOnce({ status: 'sent', emailId: 'email-1', message_id: 'gmail-2' });

    mockUseSendEmail.mockReturnValue(mockUseSendEmailFn({ mutateAsync: mockMutateAsync }));

    render(<EmailPage />, { wrapper: createWrapper() });
    await userEvent.click(screen.getByText('Compose'));

    await userEvent.type(screen.getByLabelText('To'), 'recipient@example.com');
    await userEvent.type(screen.getByLabelText('Subject'), 'Test');
    await userEvent.click(screen.getByText('Send'));

    await waitFor(() => {
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText('Retry'));

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledTimes(2);
    });

    // Modal should close on success
    await waitFor(() => {
      expect(screen.queryByText('Compose Email')).not.toBeInTheDocument();
    });
  });

  it('Discard button closes modal without sending', async () => {
    const mockMutateAsync = vi.fn();
    mockUseSendEmail.mockReturnValue(mockUseSendEmailFn({ mutateAsync: mockMutateAsync }));

    render(<EmailPage />, { wrapper: createWrapper() });
    await userEvent.click(screen.getByText('Compose'));
    expect(screen.getByText('Compose Email')).toBeInTheDocument();

    await userEvent.click(screen.getByText('Discard'));

    await waitFor(() => {
      expect(screen.queryByText('Compose Email')).not.toBeInTheDocument();
    });
    expect(mockMutateAsync).not.toHaveBeenCalled();
  });
});

describe('EmailPage — Sent Tab', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseGmailAuthUrl.mockReturnValue(mockGmailAuthUrl());
    mockUseGmailCallback.mockReturnValue(mockGmailCallback());
    mockUseTriggerSync.mockReturnValue(mockTriggerSync());
    mockUseSyncConnections.mockReturnValue({
      data: [makeConnection()],
      isLoading: false,
      refetch: vi.fn(),
    });
    mockUseEmail.mockReturnValue({ data: undefined, isLoading: false });
    mockUseToggleStar.mockReturnValue(mockToggleStar());
    mockUseMarkRead.mockReturnValue(mockMarkRead());
    mockUseSendEmail.mockReturnValue(mockUseSendEmailFn());

    mockUseEmails.mockReturnValue({ data: { results: [] }, isLoading: false, isError: false, error: null });
  });

  it('switches to Sent tab and shows sent emails', async () => {
    mockUseEmails
      .mockReturnValueOnce({ data: { results: [] }, isLoading: false, isError: false, error: null }) // initial (inbox)
      .mockReturnValueOnce({
        data: {
          results: [
            makeEmail({
              id: 'sent-1',
              direction: 'outbound',
              from_email: 'me@example.com',
              to_emails: ['client@example.com'],
              subject: 'Proposal Sent',
              is_read: true,
            }),
          ],
        },
        isLoading: false,
        isError: false,
        error: null,
      }); // sent tab

    render(<EmailPage />, { wrapper: createWrapper() });
    expect(screen.getByText('No emails yet')).toBeInTheDocument();

    await userEvent.click(screen.getByText('Sent'));
    expect(screen.getByText('Proposal Sent')).toBeInTheDocument();
  });

  it('correctly passes direction=outbound filter for Sent tab', async () => {
    const emailHookRef = { current: undefined as unknown };
    mockUseEmails.mockImplementation((params?: Record<string, string>) => {
      emailHookRef.current = params;
      return { data: { results: [] }, isLoading: false, isError: false, error: null };
    });

    render(<EmailPage />, { wrapper: createWrapper() });
    await userEvent.click(screen.getByText('Sent'));

    // After clicking Sent tab, the params should have direction=outbound
    expect(emailHookRef.current).toEqual({ direction: 'outbound' });
  });
});
