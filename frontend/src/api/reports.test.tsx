import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useDashboardReport, useForecast, useStaleDeals } from './reports';
import apiClient from './client';

vi.mock('./client', () => ({
  default: {
    get: vi.fn(),
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

describe('useDashboardReport', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls /reports/dashboard/ with no params', () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: {} });
    renderHook(() => useDashboardReport(), { wrapper: createWrapper() });
    expect(apiClient.get).toHaveBeenCalledWith('/reports/dashboard/', { params: undefined });
  });

  it('passes start_date and end_date params', () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: {} });
    renderHook(() => useDashboardReport({ start_date: '2024-01-01', end_date: '2024-01-31' }), {
      wrapper: createWrapper(),
    });
    expect(apiClient.get).toHaveBeenCalledWith('/reports/dashboard/', {
      params: { start_date: '2024-01-01', end_date: '2024-01-31' },
    });
  });

  it('passes pipeline_id and group_by params', () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: {} });
    renderHook(
      () =>
        useDashboardReport({
          pipeline_id: 'abc-123',
          group_by: 'owner',
        }),
      { wrapper: createWrapper() },
    );
    expect(apiClient.get).toHaveBeenCalledWith('/reports/dashboard/', {
      params: { pipeline_id: 'abc-123', group_by: 'owner' },
    });
  });

  it('returns DashboardReport data on success', async () => {
    const mockReport = {
      summary: { total_pipeline_value: 100000, won_value: 50000 },
      pipeline_value_trend: [],
    };
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockReport });
    const { result } = renderHook(() => useDashboardReport(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.data).toEqual(mockReport));
  });

  it('handles API error gracefully', async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new Error('Network error'));
    const { result } = renderHook(() => useDashboardReport(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.error).toBeDefined());
  });
});

describe('useStaleDeals', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls /reports/stale-deals/ with default params', () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: {} });
    renderHook(() => useStaleDeals(), { wrapper: createWrapper() });
    expect(apiClient.get).toHaveBeenCalledWith('/reports/stale-deals/', { params: undefined });
  });

  it('passes custom params', () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: {} });
    renderHook(() => useStaleDeals({ days_since_activity: '7', limit: '10', past_close_date: 'true' }), {
      wrapper: createWrapper(),
    });
    expect(apiClient.get).toHaveBeenCalledWith('/reports/stale-deals/', {
      params: { days_since_activity: '7', limit: '10', past_close_date: 'true' },
    });
  });

  it('returns StaleDealsResponse data on success', async () => {
    const mockResponse = {
      stale_deals: [
        {
          id: '1',
          name: 'Test Deal',
          value: 10000,
          stage_name: 'Negotiation',
          owner_name: 'Alice',
          days_in_stage: 5,
          days_since_last_activity: 12,
          expected_close_date: '2024-06-01',
          is_overdue: false,
        },
      ],
    };
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });
    const { result } = renderHook(() => useStaleDeals(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.data).toEqual(mockResponse));
  });

  it('handles API error gracefully', async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new Error('Not found'));
    const { result } = renderHook(() => useStaleDeals(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.error).toBeDefined());
  });
});

describe('useForecast', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls /reports/forecast/ with default params', () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: {} });
    renderHook(() => useForecast(), { wrapper: createWrapper() });
    expect(apiClient.get).toHaveBeenCalledWith('/reports/forecast/', { params: undefined });
  });

  it('passes range and confidence_level params', () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: {} });
    renderHook(() => useForecast({ range: 'year', confidence_level: 'optimistic' }), {
      wrapper: createWrapper(),
    });
    expect(apiClient.get).toHaveBeenCalledWith('/reports/forecast/', {
      params: { range: 'year', confidence_level: 'optimistic' },
    });
  });

  it('passes pipeline_id and what-if params', () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: {} });
    renderHook(
      () =>
        useForecast({
          pipeline_id: 'abc-123',
          scenario_stage: 'Negotiation',
          scenario_close_rate: 0.8,
        }),
      { wrapper: createWrapper() },
    );
    expect(apiClient.get).toHaveBeenCalledWith('/reports/forecast/', {
      params: { pipeline_id: 'abc-123', scenario_stage: 'Negotiation', scenario_close_rate: 0.8 },
    });
  });

  it('returns ForecastResponse data on success', async () => {
    const mockForecast = {
      period: { quarter: '2026-Q3', start_date: '2026-07-01', end_date: '2026-09-30', label: 'Next 3 Months' },
      projections: {
        simple_weighted: { projected_revenue: 145000, deals_in_pipeline: 10, total_pipeline_value: 500000, description: 'Sum of value × probability' },
        win_rate_adjusted: { projected_revenue: 101500, historical_win_rate: 0.7, adjustment_factor: 0.7, description: 'Weighted × win rate' },
        velocity_based: { projected_revenue: 160000, expected_close_count: 6, deals_with_expected_dates: 8, avg_days_to_close: 45.2, monthly_breakdown: [{ month: '2026-07', projected_value: 50000, expected_deals: 2 }] },
      },
      scenario: null,
      what_if: null,
      deal_forecasts: [],
    };
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockForecast });
    const { result } = renderHook(() => useForecast(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.data).toEqual(mockForecast));
  });

  it('handles API error gracefully', async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new Error('API error'));
    const { result } = renderHook(() => useForecast(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.error).toBeDefined());
  });
});