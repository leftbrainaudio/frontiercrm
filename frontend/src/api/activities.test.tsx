import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useActivityTimeline, useActivities, useCreateActivity } from './activities';
import apiClient from './client';

vi.mock('./client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('useActivityTimeline', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls /activities/timeline/ with no params', () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: {} });
    renderHook(() => useActivityTimeline(), { wrapper: createWrapper() });
    expect(apiClient.get).toHaveBeenCalledWith('/activities/timeline/', { params: undefined });
  });

  it('passes all timeline params', () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: {} });
    renderHook(
      () =>
        useActivityTimeline({
          start_date: '2026-01-01',
          end_date: '2026-06-30',
          activity_type: 'note',
          actor_id: 'abc-123',
          page: 2,
          page_size: 50,
        }),
      { wrapper: createWrapper() },
    );
    expect(apiClient.get).toHaveBeenCalledWith('/activities/timeline/', {
      params: {
        start_date: '2026-01-01',
        end_date: '2026-06-30',
        activity_type: 'note',
        actor_id: 'abc-123',
        page: 2,
        page_size: 50,
      },
    });
  });

  it('returns TimelineResponse data on success', async () => {
    const mockResponse = {
      count: 3,
      page: 1,
      page_size: 25,
      total_pages: 1,
      next: null,
      previous: null,
      results: [
        {
          id: 'a1',
          activity_type: 'note',
          title: 'Test note',
          description: 'A test',
          created_at: '2026-06-30T12:00:00Z',
          actor: { id: 'u1', name: 'Alice', avatar_url: '' },
          entity: { type: 'contact', id: 'c1', name: 'Bob', url: '/contacts/c1' },
          metadata: {},
        },
      ],
    };
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });
    const { result } = renderHook(() => useActivityTimeline(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.data).toEqual(mockResponse));
  });

  it('handles API error gracefully', async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new Error('Network error'));
    const { result } = renderHook(() => useActivityTimeline(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.error).toBeDefined());
  });

  it('passes activity_type param to API call', () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: {} });
    renderHook(
      () => useActivityTimeline({ activity_type: 'call' }),
      { wrapper: createWrapper() },
    );
    expect(apiClient.get).toHaveBeenCalledWith('/activities/timeline/', {
      params: { activity_type: 'call' },
    });
  });
});

describe('useActivities', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls /activities/ with params', () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: { count: 0, results: [] } });
    renderHook(() => useActivities({ activity_type: 'note' }), { wrapper: createWrapper() });
    expect(apiClient.get).toHaveBeenCalledWith('/activities/', {
      params: { activity_type: 'note' },
    });
  });
});

describe('useCreateActivity', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls POST /activities/ with data', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ data: { id: 'new-id' } });
    const { result } = renderHook(() => useCreateActivity(), { wrapper: createWrapper() });

    await result.current.mutateAsync({
      activity_type: 'note',
      title: 'New note',
      entity_type: 'contact',
      entity_id: 'e1',
    });

    expect(apiClient.post).toHaveBeenCalledWith('/activities/', {
      activity_type: 'note',
      title: 'New note',
      entity_type: 'contact',
      entity_id: 'e1',
    });
  });
});