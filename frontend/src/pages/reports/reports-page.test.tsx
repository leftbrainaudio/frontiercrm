import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'react';
import { ReportsPage } from './reports-page';

// Mock the API hooks
vi.mock('../../api/reports', () => ({
  useDashboardReport: vi.fn(),
  useStaleDeals: vi.fn(),
  useForecast: vi.fn(),
}));

vi.mock('../../api/deals', () => ({
  usePipelines: vi.fn(),
}));

import { useDashboardReport, useStaleDeals, useForecast } from '../../api/reports';
import { usePipelines } from '../../api/deals';

function createWrapper(initialRoute = '/reports') {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[initialRoute]}>{children}</MemoryRouter>
      </QueryClientProvider>
    );
  };
}

describe('ReportsPage integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the report header with title', () => {
    vi.mocked(useDashboardReport).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useDashboardReport>);
    vi.mocked(useStaleDeals).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useStaleDeals>);
    vi.mocked(usePipelines).mockReturnValue({
      data: [],
      isLoading: false,
    } as ReturnType<typeof usePipelines>);

    render(<ReportsPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Reports & Analytics')).toBeInTheDocument();
  });

  it('renders date range preset buttons', () => {
    vi.mocked(useDashboardReport).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useDashboardReport>);
    vi.mocked(useStaleDeals).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useStaleDeals>);
    vi.mocked(usePipelines).mockReturnValue({
      data: [],
      isLoading: false,
    } as ReturnType<typeof usePipelines>);

    render(<ReportsPage />, { wrapper: createWrapper() });
    expect(screen.getByText('7d')).toBeInTheDocument();
    expect(screen.getByText('30d')).toBeInTheDocument();
    expect(screen.getByText('90d')).toBeInTheDocument();
    expect(screen.getByText('This Q')).toBeInTheDocument();
  });

  it('renders pipeline filter and group-by select', () => {
    vi.mocked(useDashboardReport).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useDashboardReport>);
    vi.mocked(useStaleDeals).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useStaleDeals>);
    vi.mocked(usePipelines).mockReturnValue({
      data: [],
      isLoading: false,
    } as ReturnType<typeof usePipelines>);

    render(<ReportsPage />, { wrapper: createWrapper() });
    expect(screen.getByText('All Pipelines')).toBeInTheDocument();
    expect(screen.getByText('Group: None')).toBeInTheDocument();
    expect(screen.getByText('Group: Owner')).toBeInTheDocument();
  });

  it('renders empty states for all sections when no data', () => {
    vi.mocked(useDashboardReport).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useDashboardReport>);
    vi.mocked(useStaleDeals).mockReturnValue({
      data: { stale_deals: [] },
      isLoading: false,
      error: null,
    } as ReturnType<typeof useStaleDeals>);
    vi.mocked(usePipelines).mockReturnValue({
      data: [],
      isLoading: false,
    } as ReturnType<typeof usePipelines>);

    render(<ReportsPage />, { wrapper: createWrapper() });
    // Empty states for chart sections (default empty arrays → empty states)
    expect(screen.getByText('Pipeline Value Over Time')).toBeInTheDocument();
    expect(screen.getByText('No pipeline data for this period')).toBeInTheDocument();
    expect(screen.getByText('No stage data available')).toBeInTheDocument();
    expect(screen.getByText('No conversion data available')).toBeInTheDocument();
    expect(screen.getByText('No deal velocity data available')).toBeInTheDocument();
    expect(screen.getByText('No activities in this period')).toBeInTheDocument();
    expect(screen.getByText('No activity data by day')).toBeInTheDocument();
  });

  it('renders metric cards with data from report', () => {
    vi.mocked(useDashboardReport).mockReturnValue({
      data: {
        period: { start_date: '2024-01-01', end_date: '2024-01-31', label: 'Jan 2024' },
        summary: {
          total_pipeline_value: 500000,
          pipeline_value_change: 12.5,
          won_value: 200000,
          won_value_change: 8.3,
          lost_value: 50000,
          win_rate: 0.4,
          win_rate_change: 0.05,
          active_deals: 25,
          active_deals_change: 3,
          avg_deal_value: 20000,
          avg_deal_value_change: 1.5,
          avg_days_to_close: 35,
          weighted_pipeline: 300000,
        },
        pipeline_value_trend: [],
        deals_by_stage: [],
        win_rate_by_stage: [],
        deal_velocity: [],
        activity_metrics: {
          total: 0,
          by_type: [],
          by_day: [],
          calls_with_duration: { total_minutes: 0, avg_minutes: 0 },
        },
        tasks_summary: { total_due: 0, overdue: 0, due_today: 0, by_priority: {} },
      },
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useDashboardReport>);
    vi.mocked(useStaleDeals).mockReturnValue({
      data: { stale_deals: [] },
      isLoading: false,
      error: null,
    } as ReturnType<typeof useStaleDeals>);
    vi.mocked(usePipelines).mockReturnValue({
      data: [],
      isLoading: false,
    } as ReturnType<typeof usePipelines>);

    render(<ReportsPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Pipeline Value')).toBeInTheDocument();
    expect(screen.getByText('$500,000')).toBeInTheDocument();
    expect(screen.getByText('Win Rate')).toBeInTheDocument();
    expect(screen.getByText('40%')).toBeInTheDocument();
    expect(screen.getByText('Active Deals')).toBeInTheDocument();
    expect(screen.getByText('25')).toBeInTheDocument();
  });

  it('renders top performers table when by_owner data present', () => {
    vi.mocked(useDashboardReport).mockReturnValue({
      data: {
        period: { start_date: '2024-01-01', end_date: '2024-01-31', label: 'Jan 2024' },
        summary: {
          total_pipeline_value: 500000,
          pipeline_value_change: null,
          won_value: 200000,
          won_value_change: null,
          lost_value: 50000,
          win_rate: 0.4,
          win_rate_change: null,
          active_deals: 25,
          active_deals_change: null,
          avg_deal_value: 20000,
          avg_deal_value_change: null,
          avg_days_to_close: 35,
          weighted_pipeline: 300000,
        },
        pipeline_value_trend: [],
        deals_by_stage: [],
        win_rate_by_stage: [],
        deal_velocity: [],
        activity_metrics: {
          total: 0,
          by_type: [],
          by_day: [],
          calls_with_duration: { total_minutes: 0, avg_minutes: 0 },
        },
        tasks_summary: { total_due: 0, overdue: 0, due_today: 0, by_priority: {} },
        by_owner: [
          {
            owner_id: 'u1',
            owner_name: 'Alice',
            pipeline_value: 250000,
            won_value: 100000,
            win_rate: 0.6,
            active_deals: 10,
            won_deals: 6,
            lost_deals: 4,
            avg_deal_value: 25000,
            activity_count: 30,
          },
        ],
      },
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useDashboardReport>);
    vi.mocked(useStaleDeals).mockReturnValue({
      data: { stale_deals: [] },
      isLoading: false,
      error: null,
    } as ReturnType<typeof useStaleDeals>);
    vi.mocked(usePipelines).mockReturnValue({
      data: [],
      isLoading: false,
    } as ReturnType<typeof usePipelines>);

    render(<ReportsPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Rep Performance')).toBeInTheDocument();
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('$250,000')).toBeInTheDocument();
  });

  it('renders pipeline options from usePipelines hook', () => {
    vi.mocked(useDashboardReport).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useDashboardReport>);
    vi.mocked(useStaleDeals).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useStaleDeals>);
    vi.mocked(usePipelines).mockReturnValue({
      data: [
        { id: 'pipe-1', name: 'Enterprise Sales' },
        { id: 'pipe-2', name: 'SMB Sales' },
      ],
      isLoading: false,
    } as unknown as ReturnType<typeof usePipelines>);

    render(<ReportsPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Enterprise Sales')).toBeInTheDocument();
    expect(screen.getByText('SMB Sales')).toBeInTheDocument();
  });
});