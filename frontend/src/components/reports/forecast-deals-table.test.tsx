import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ForecastDealsTable } from '../../components/reports/forecast-deals-table';
import type { DealForecast } from '../../types';

// The component uses formatCurrency/formatPercent from shared
// Those are pure utility functions that don't need mocking

const mockDeals: DealForecast[] = [
  {
    deal_id: 'd1',
    deal_name: 'Big Corp Deal',
    deal_value: 100000,
    stage_name: 'Negotiation',
    stage_probability: 0.8,
    probability_weight: 0.8,
    projected_value: 80000,
    estimated_close_date: '2026-08-15',
    pipeline_name: 'Sales Pipeline',
    has_expected_date: true,
  },
  {
    deal_id: 'd2',
    deal_name: 'Small Startup',
    deal_value: 25000,
    stage_name: 'Proposal',
    stage_probability: 0.6,
    probability_weight: 0.6,
    projected_value: 15000,
    estimated_close_date: null,
    pipeline_name: 'Sales Pipeline',
    has_expected_date: false,
  },
  {
    deal_id: 'd3',
    deal_name: 'Mid Tier',
    deal_value: 50000,
    stage_name: 'Qualified',
    stage_probability: 0.25,
    probability_weight: 0.25,
    projected_value: 12500,
    estimated_close_date: '2026-09-01',
    pipeline_name: 'Other Pipeline',
    has_expected_date: false,
  },
];

describe('ForecastDealsTable loading state', () => {
  it('renders skeleton animation when loading', () => {
    const { container } = render(<ForecastDealsTable deals={[]} loading={true} />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders skeleton heading placeholder', () => {
    const { container } = render(<ForecastDealsTable deals={[]} loading={true} />);
    const skeletonHeaders = container.querySelectorAll('.animate-pulse');
    expect(skeletonHeaders.length).toBeGreaterThanOrEqual(2);
  });
});

describe('ForecastDealsTable empty state', () => {
  it('returns null when deals array is empty', () => {
    const { container } = render(<ForecastDealsTable deals={[]} />);
    expect(container.innerHTML).toBe('');
  });

  it('returns null when deals is undefined', () => {
    const { container } = render(
      <ForecastDealsTable deals={undefined as unknown as DealForecast[]} />,
    );
    expect(container.innerHTML).toBe('');
  });
});

describe('ForecastDealsTable with data', () => {
  beforeEach(() => {});

  it('renders the table title', () => {
    render(<ForecastDealsTable deals={mockDeals} />);
    expect(screen.getByText('Deal-by-Deal Forecast')).toBeInTheDocument();
  });

  it('renders all deal names', () => {
    render(<ForecastDealsTable deals={mockDeals} />);
    expect(screen.getByText('Big Corp Deal')).toBeInTheDocument();
    expect(screen.getByText('Small Startup')).toBeInTheDocument();
    expect(screen.getByText('Mid Tier')).toBeInTheDocument();
  });

  it('renders stage names', () => {
    render(<ForecastDealsTable deals={mockDeals} />);
    expect(screen.getByText('Negotiation')).toBeInTheDocument();
    expect(screen.getByText('Proposal')).toBeInTheDocument();
    expect(screen.getByText('Qualified')).toBeInTheDocument();
  });

  it('renders pipeline names', () => {
    render(<ForecastDealsTable deals={mockDeals} />);
    // Sales Pipeline appears for 2 deals
    const salesPipelines = screen.getAllByText('Sales Pipeline');
    expect(salesPipelines.length).toBe(2);
    expect(screen.getByText('Other Pipeline')).toBeInTheDocument();
  });

  it('renders deal values as currency', () => {
    render(<ForecastDealsTable deals={mockDeals} />);
    expect(screen.getByText('$100,000')).toBeInTheDocument();
    expect(screen.getByText('$25,000')).toBeInTheDocument();
    expect(screen.getByText('$50,000')).toBeInTheDocument();
  });

  it('renders probability weights as percentages', () => {
    render(<ForecastDealsTable deals={mockDeals} />);
    expect(screen.getByText('80%')).toBeInTheDocument();
    expect(screen.getByText('60%')).toBeInTheDocument();
    expect(screen.getByText('25%')).toBeInTheDocument();
  });

  it('renders projected values as currency', () => {
    render(<ForecastDealsTable deals={mockDeals} />);
    expect(screen.getByText('$80,000')).toBeInTheDocument();
    expect(screen.getByText('$15,000')).toBeInTheDocument();
    expect(screen.getByText('$12,500')).toBeInTheDocument();
  });

  it('renders formatted close dates', () => {
    render(<ForecastDealsTable deals={mockDeals} />);
    expect(screen.getByText('Aug 15, 2026')).toBeInTheDocument();
    expect(screen.getByText('Sep 1, 2026')).toBeInTheDocument();
  });

  it('renders dash for deals without close dates', () => {
    render(<ForecastDealsTable deals={mockDeals} />);
    const dashes = screen.getAllByText('—');
    expect(dashes.length).toBeGreaterThanOrEqual(1);
  });

  it('shows tilde indicator for estimated dates without expected dates', () => {
    render(<ForecastDealsTable deals={mockDeals} />);
    // Mid Tier has has_expected_date=false, so should show ~ indicator
    const tildeElements = document.querySelectorAll('.text-amber-500');
    expect(tildeElements.length).toBeGreaterThanOrEqual(1);
    expect(tildeElements[0].textContent).toContain('~');
  });

  it('shows deal count in footer', () => {
    render(<ForecastDealsTable deals={mockDeals} />);
    expect(screen.getByText(/Showing 3 open deals/)).toBeInTheDocument();
  });

  it('uses singular "deal" when only one deal', () => {
    render(<ForecastDealsTable deals={[mockDeals[0]]} />);
    expect(screen.getByText(/Showing 1 open deal/)).toBeInTheDocument();
  });

  it('renders all table column headers', () => {
    render(<ForecastDealsTable deals={mockDeals} />);
    const headers = ['Deal', 'Stage', 'Pipeline', 'Value', 'Prob.', 'Weighted', 'Est. Close'];
    for (const header of headers) {
      expect(screen.getByText(header)).toBeInTheDocument();
    }
  });
});