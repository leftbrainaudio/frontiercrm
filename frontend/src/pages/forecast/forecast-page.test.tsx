import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

// Mock API hooks before imports
vi.mock('../../api/deals', () => ({
  usePipelines: vi.fn(),
}));

vi.mock('../../api/reports', () => ({
  useForecast: vi.fn(),
}));

import { ForecastPage } from './forecast-page';
import { usePipelines } from '../../api/deals';
import { useForecast } from '../../api/reports';

const mockPipelines = [
  {
    id: 'pipe-1',
    name: 'Sales Pipeline',
    stages: [
      { id: 's1', name: 'Qualified' },
      { id: 's2', name: 'Proposal' },
      { id: 's3', name: 'Negotiation' },
    ],
  },
];

const mockForecastData = {
  period: {
    quarter: 'Next 3 Months',
    start_date: '2026-07-01',
    end_date: '2026-09-30',
    label: 'Next 3 Months',
  },
  projections: {
    simple_weighted: {
      projected_revenue: 145000,
      deals_in_pipeline: 10,
      total_pipeline_value: 500000,
      description: 'Sum of value × probability for all open deals',
    },
    win_rate_adjusted: {
      projected_revenue: 101500,
      historical_win_rate: 0.7,
      adjustment_factor: 0.7,
      description: 'Weighted pipeline × historical win rate',
    },
    velocity_based: {
      projected_revenue: 160000,
      expected_close_count: 6,
      deals_with_expected_dates: 8,
      avg_days_to_close: 45.2,
      monthly_breakdown: [
        { month: '2026-07', projected_value: 50000, expected_deals: 2 },
        { month: '2026-08', projected_value: 75000, expected_deals: 3 },
        { month: '2026-09', projected_value: 35000, expected_deals: 1 },
      ],
    },
  },
  scenario: null,
  what_if: null,
  deal_forecasts: [
    {
      deal_id: 'd1',
      deal_name: 'Big Deal',
      deal_value: 100000,
      stage_name: 'Negotiation',
      stage_probability: 0.8,
      probability_weight: 0.8,
      projected_value: 80000,
      estimated_close_date: '2026-08-15',
      pipeline_name: 'Sales Pipeline',
      has_expected_date: true,
    },
  ],
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

function setupLoading() {
  vi.mocked(usePipelines).mockReturnValue({ data: undefined, isLoading: false });
  vi.mocked(useForecast).mockReturnValue({ data: undefined, isLoading: true });
}

function setupEmpty() {
  vi.mocked(usePipelines).mockReturnValue({ data: undefined, isLoading: false });
  vi.mocked(useForecast).mockReturnValue({ data: undefined, isLoading: false });
}

function setupWithData(overrides: Record<string, unknown> = {}) {
  vi.mocked(usePipelines).mockReturnValue({ data: mockPipelines, isLoading: false });
  vi.mocked(useForecast).mockReturnValue({
    data: { ...mockForecastData, ...overrides },
    isLoading: false,
  });
}

// ── Loading State ────────────────────────────────────────────────────

describe('ForecastPage loading state', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupLoading();
  });

  it('renders skeleton loading elements when loading', () => {
    const { container } = render(<ForecastPage />, { wrapper: createWrapper() });
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('shows skeleton layout with header placeholder', () => {
    render(<ForecastPage />, { wrapper: createWrapper() });
    expect(document.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0);
  });
});

// ── Empty State ──────────────────────────────────────────────────────

describe('ForecastPage empty state', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupEmpty();
  });

  it('renders empty state message when no forecast data', () => {
    render(<ForecastPage />, { wrapper: createWrapper() });
    expect(screen.getByText('No Forecast Data')).toBeInTheDocument();
  });

  it('renders helpful empty state description', () => {
    render(<ForecastPage />, { wrapper: createWrapper() });
    expect(
      screen.getByText(/No deals match the current filter criteria/i),
    ).toBeInTheDocument();
  });
});

// ── With Data ────────────────────────────────────────────────────────

describe('ForecastPage with data', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupWithData();
  });

  it('renders page title', () => {
    render(<ForecastPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Pipeline Forecast')).toBeInTheDocument();
  });

  it('renders period information in the page subtitle', () => {
    render(<ForecastPage />, { wrapper: createWrapper() });
    // The period info is nested inside the p element below the h1.
    const subtitle = screen.getByText(/2026-07-01.*2026-09-30/);
    expect(subtitle).toBeInTheDocument();
  });

  it('renders summary cards with projected revenue', () => {
    render(<ForecastPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Projected Revenue')).toBeInTheDocument();
    expect(screen.getByText('Weighted Pipeline')).toBeInTheDocument();
    expect(screen.getByText('Win-Rate Adjusted')).toBeInTheDocument();
    expect(screen.getByText('Expected Deals Closed')).toBeInTheDocument();
  });

  it('renders the revenue chart section', () => {
    render(<ForecastPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Revenue Projection — Monthly Breakdown')).toBeInTheDocument();
  });

  it('renders what-if scenario section', () => {
    render(<ForecastPage />, { wrapper: createWrapper() });
    expect(screen.getByText('What-If Scenario')).toBeInTheDocument();
  });

  it('renders the deal-by-deal table', () => {
    render(<ForecastPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Deal-by-Deal Forecast')).toBeInTheDocument();
    expect(screen.getByText('Big Deal')).toBeInTheDocument();
  });

  it('renders monthly breakdown table', () => {
    render(<ForecastPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Monthly Breakdown')).toBeInTheDocument();
  });

  it('renders all three forecast range buttons', () => {
    render(<ForecastPage />, { wrapper: createWrapper() });
    // The range buttons are <button> elements inside a segmented control
    const rangeButtons = screen.getAllByRole('button').filter(
      (b) => b.textContent === 'Next 3 Months'
        || b.textContent === 'Next 6 Months'
        || b.textContent === 'Next 12 Months',
    );
    const buttonLabels = rangeButtons.map((b) => b.textContent);
    expect(buttonLabels).toContain('Next 3 Months');
    expect(buttonLabels).toContain('Next 6 Months');
    expect(buttonLabels).toContain('Next 12 Months');
  });

  it('renders scenario toggle buttons (Worst Case, Most Likely, Best Case)', () => {
    render(<ForecastPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Worst Case')).toBeInTheDocument();
    expect(screen.getByText('Most Likely')).toBeInTheDocument();
    expect(screen.getByText('Best Case')).toBeInTheDocument();
  });

  it('renders pipeline filter dropdown with All Pipelines option', () => {
    render(<ForecastPage />, { wrapper: createWrapper() });
    const allPipelines = screen.getAllByText('All Pipelines');
    expect(allPipelines.length).toBeGreaterThanOrEqual(1);
    // Sales Pipeline appears as option AND as pipeline_name in the deals table
    const salesOptions = screen.getAllByText('Sales Pipeline');
    expect(salesOptions.length).toBeGreaterThanOrEqual(1);
  });

  it('renders export CSV button', () => {
    render(<ForecastPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Export CSV')).toBeInTheDocument();
  });
});

// ── Scenario Toggles ─────────────────────────────────────────────────

describe('ForecastPage scenario toggles', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupWithData();
  });

  it('shows Most Likely as default scenario in the period subtitle', () => {
    render(<ForecastPage />, { wrapper: createWrapper() });
    // The period subtitle contains the scenario info
    expect(screen.getByText(/Scenario: Most Likely/)).toBeInTheDocument();
  });

  it('clicking Best Case updates the query params', async () => {
    const user = userEvent.setup();
    vi.mocked(useForecast).mockClear();
    render(<ForecastPage />, { wrapper: createWrapper() });
    await user.click(screen.getByText('Best Case'));
    expect(useForecast).toHaveBeenLastCalledWith(
      expect.objectContaining({ confidence_level: 'optimistic' }),
    );
  });

  it('clicking Worst Case updates the query params', async () => {
    const user = userEvent.setup();
    vi.mocked(useForecast).mockClear();
    render(<ForecastPage />, { wrapper: createWrapper() });
    await user.click(screen.getByText('Worst Case'));
    expect(useForecast).toHaveBeenLastCalledWith(
      expect.objectContaining({ confidence_level: 'conservative' }),
    );
  });
});

// ── Range Selector ───────────────────────────────────────────────────

describe('ForecastPage range selector', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupWithData();
  });

  it('clicking Next 6 Months button changes range', async () => {
    const user = userEvent.setup();
    vi.mocked(useForecast).mockClear();
    render(<ForecastPage />, { wrapper: createWrapper() });
    await user.click(screen.getByText('Next 6 Months'));
    expect(useForecast).toHaveBeenLastCalledWith(
      expect.objectContaining({ range: 'half-year' }),
    );
  });

  it('clicking Next 12 Months button changes range', async () => {
    const user = userEvent.setup();
    vi.mocked(useForecast).mockClear();
    render(<ForecastPage />, { wrapper: createWrapper() });
    await user.click(screen.getByText('Next 12 Months'));
    expect(useForecast).toHaveBeenLastCalledWith(
      expect.objectContaining({ range: 'year' }),
    );
  });
});

// ── Pipeline Filter ──────────────────────────────────────────────────

describe('ForecastPage pipeline filter', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupWithData();
  });

  it('selecting a pipeline updates query params', async () => {
    const user = userEvent.setup();
    vi.mocked(useForecast).mockClear();
    render(<ForecastPage />, { wrapper: createWrapper() });

    // Pipeline filter is the first select element (before the stage selector)
    const selects = screen.getAllByRole('combobox');
    const pipelineSelect = selects[0];
    await user.selectOptions(pipelineSelect, 'pipe-1');

    expect(useForecast).toHaveBeenLastCalledWith(
      expect.objectContaining({ pipeline_id: 'pipe-1' }),
    );
  });

  it('selecting All Pipelines removes pipeline_id from params', async () => {
    const user = userEvent.setup();
    vi.mocked(useForecast).mockClear();
    render(<ForecastPage />, { wrapper: createWrapper() });

    const selects = screen.getAllByRole('combobox');
    const pipelineSelect = selects[0];
    await user.selectOptions(pipelineSelect, '');
    expect(useForecast).toHaveBeenLastCalledWith(
      expect.not.objectContaining({ pipeline_id: expect.any(String) }),
    );
  });
});

// ── What-If Slider ───────────────────────────────────────────────────

describe('ForecastPage what-if slider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupWithData();
  });

  it('renders stage dropdown for what-if', () => {
    render(<ForecastPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Select a stage...')).toBeInTheDocument();
  });

  it('renders stage options from pipelines', () => {
    render(<ForecastPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Qualified')).toBeInTheDocument();
    expect(screen.getByText('Proposal')).toBeInTheDocument();
    // Negotiation also appears in the deal table, so use getAllByText
    const matches = screen.getAllByText('Negotiation');
    expect(matches.length).toBeGreaterThanOrEqual(1);
  });

  it('renders what-if close rate slider', () => {
    render(<ForecastPage />, { wrapper: createWrapper() });
    const slider = document.querySelector('input[type="range"]');
    expect(slider).toBeInTheDocument();
  });

  it('selecting a stage adds scenario_stage to query params', async () => {
    const user = userEvent.setup();
    vi.mocked(useForecast).mockClear();
    render(<ForecastPage />, { wrapper: createWrapper() });

    const stageSelect = screen.getByDisplayValue('Select a stage...');
    await user.selectOptions(stageSelect, 'Negotiation');

    expect(useForecast).toHaveBeenLastCalledWith(
      expect.objectContaining({
        scenario_stage: 'Negotiation',
        scenario_close_rate: 0.5,
      }),
    );
  });

  it('changing slider value updates scenario_close_rate in query', async () => {
    const user = userEvent.setup();
    vi.mocked(useForecast).mockClear();
    render(<ForecastPage />, { wrapper: createWrapper() });

    // First select a stage so what-if mode is active
    const stageSelect = screen.getByDisplayValue('Select a stage...');
    await user.selectOptions(stageSelect, 'Negotiation');

    vi.mocked(useForecast).mockClear();

    // Change the slider
    const slider = document.querySelector('input[type="range"]') as HTMLInputElement;
    expect(slider).not.toBeNull();
    fireEvent.change(slider, { target: { value: '0.75' } });

    expect(useForecast).toHaveBeenLastCalledWith(
      expect.objectContaining({ scenario_close_rate: 0.75 }),
    );
  });

  it('displays close rate label as percentage', () => {
    render(<ForecastPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Close Rate: 50%')).toBeInTheDocument();
  });

  it('shows what-if results when stage is selected and what_if data is provided', () => {
    vi.mocked(useForecast).mockReturnValue({
      data: {
        ...mockForecastData,
        what_if: {
          stage_name: 'Negotiation',
          current_close_rate: 0.8,
          scenario_close_rate: 0.9,
          deals_affected: 3,
          current_projected_value: 400000,
          scenario_projected_value: 450000,
          upside: 50000,
        },
      },
      isLoading: false,
    });
    render(<ForecastPage />, { wrapper: createWrapper() });
    fireEvent.change(screen.getByDisplayValue('Select a stage...'), {
      target: { value: 'Negotiation' },
    });
    expect(screen.getByText(/Deals affected: 3/)).toBeInTheDocument();
    expect(screen.getByText(/Upside/)).toBeInTheDocument();
  });

  it('shows fallback message when stage selected but no deals found', async () => {
    const user = userEvent.setup();
    vi.mocked(useForecast).mockReturnValue({
      data: {
        ...mockForecastData,
        what_if: null,
      },
      isLoading: false,
    });
    render(<ForecastPage />, { wrapper: createWrapper() });
    const stageSelect = screen.getByDisplayValue('Select a stage...');
    await user.selectOptions(stageSelect, 'Negotiation');
    // Should show the "No deals found in stage" fallback message
    expect(screen.getByText(/No deals found in stage/)).toBeInTheDocument();
  });
});

// ── What-If Data ─────────────────────────────────────────────────────

describe('ForecastPage with what-if data', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useForecast).mockReturnValue({
      data: {
        ...mockForecastData,
        what_if: {
          stage_name: 'Negotiation',
          current_close_rate: 0.8,
          scenario_close_rate: 0.95,
          deals_affected: 3,
          current_projected_value: 400000,
          scenario_projected_value: 475000,
          upside: 75000,
        },
      },
      isLoading: false,
    });
    vi.mocked(usePipelines).mockReturnValue({ data: mockPipelines, isLoading: false });
  });

  it('renders what-if result when data is present', () => {
    render(<ForecastPage />, { wrapper: createWrapper() });
    fireEvent.change(screen.getByDisplayValue('Select a stage...'), {
      target: { value: 'Negotiation' },
    });
    expect(screen.getByText(/Deals affected: 3/)).toBeInTheDocument();
  });
});

// ── Export CSV ───────────────────────────────────────────────────────

describe('ForecastPage export CSV', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupWithData();
  });

  it('renders export CSV button', () => {
    render(<ForecastPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Export CSV')).toBeInTheDocument();
  });

  it('clicking export CSV creates a download link', async () => {
    // Spy on URL.createObjectURL to verify a blob was created
    const createObjectURLSpy = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:test');
    const revokeSpy = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});

    render(<ForecastPage />, { wrapper: createWrapper() });
    await userEvent.click(screen.getByText('Export CSV'));

    // Should have created a blob URL
    expect(createObjectURLSpy).toHaveBeenCalledTimes(1);

    createObjectURLSpy.mockRestore();
    revokeSpy.mockRestore();
  });
});
