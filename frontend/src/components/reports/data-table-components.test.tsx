import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { DealVelocityTable } from './deal-velocity-table';
import { TopPerformersTable } from './top-performers-table';
import { StaleDealsList } from './stale-deals-list';

function Wrapper({ children }: { children: React.ReactNode }) {
  return <BrowserRouter>{children}</BrowserRouter>;
}

describe('DealVelocityTable', () => {
  const sampleData = [
    { stage_name: 'Qualified', avg_days: 8.5, deals_in_stage: 5 },
    { stage_name: 'Proposal', avg_days: 14.2, deals_in_stage: 3 },
  ];

  it('renders stage names', () => {
    render(<DealVelocityTable data={sampleData} />, { wrapper: Wrapper });
    expect(screen.getByText('Qualified')).toBeInTheDocument();
    expect(screen.getByText('Proposal')).toBeInTheDocument();
  });

  it('renders avg_days formatted', () => {
    render(<DealVelocityTable data={sampleData} />, { wrapper: Wrapper });
    expect(screen.getByText('8.5d')).toBeInTheDocument();
    expect(screen.getByText('14.2d')).toBeInTheDocument();
  });

  it('renders deals_in_stage', () => {
    render(<DealVelocityTable data={sampleData} />, { wrapper: Wrapper });
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('renders card title', () => {
    render(<DealVelocityTable data={sampleData} />, { wrapper: Wrapper });
    expect(screen.getByText('Average Time Per Stage')).toBeInTheDocument();
  });

  it('renders status labels based on avg_days thresholds', () => {
    const statusData = [
      { stage_name: 'Fast', avg_days: 3, deals_in_stage: 2 },
      { stage_name: 'Slow', avg_days: 21, deals_in_stage: 1 },
    ];
    render(<DealVelocityTable data={statusData} />, { wrapper: Wrapper });
    expect(screen.getByText('🟢 Fast')).toBeInTheDocument();
    expect(screen.getByText('🔴 Slower')).toBeInTheDocument();
  });

  it('renders dash when deals_in_stage is 0', () => {
    const data = [{ stage_name: 'Empty', avg_days: 0, deals_in_stage: 0 }];
    render(<DealVelocityTable data={data} />, { wrapper: Wrapper });
    expect(screen.getByText('—')).toBeInTheDocument();
  });
});

describe('TopPerformersTable', () => {
  const sampleData = [
    {
      owner_id: 'u1',
      owner_name: 'Alice',
      pipeline_value: 150000,
      won_value: 80000,
      win_rate: 0.6,
      active_deals: 5,
      won_deals: 3,
      lost_deals: 2,
      avg_deal_value: 30000,
      activity_count: 45,
    },
  ];

  it('renders owner_name', () => {
    render(<TopPerformersTable data={sampleData} />, { wrapper: Wrapper });
    expect(screen.getByText('Alice')).toBeInTheDocument();
  });

  it('renders pipeline_value formatted as currency', () => {
    render(<TopPerformersTable data={sampleData} />, { wrapper: Wrapper });
    expect(screen.getByText('$150,000')).toBeInTheDocument();
  });

  it('renders win_rate as percentage', () => {
    render(<TopPerformersTable data={sampleData} />, { wrapper: Wrapper });
    expect(screen.getByText('60%')).toBeInTheDocument();
  });

  it('renders active_deals count', () => {
    render(<TopPerformersTable data={sampleData} />, { wrapper: Wrapper });
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('renders activity_count', () => {
    render(<TopPerformersTable data={sampleData} />, { wrapper: Wrapper });
    expect(screen.getByText('45')).toBeInTheDocument();
  });

  it('renders card title and subtitle', () => {
    render(<TopPerformersTable data={sampleData} />, { wrapper: Wrapper });
    expect(screen.getByText('Rep Performance')).toBeInTheDocument();
    expect(screen.getByText('Per-owner breakdown')).toBeInTheDocument();
  });
});

describe('StaleDealsList', () => {
  it('renders stale deal data', () => {
    const data = [
      {
        id: 'deal-1',
        name: 'Big Corp Deal',
        value: 50000,
        stage_name: 'Negotiation',
        owner_name: 'Bob',
        days_in_stage: 10,
        days_since_last_activity: 5,
        expected_close_date: '2024-06-01',
        is_overdue: false,
      },
    ];
    render(<StaleDealsList data={data} />, { wrapper: Wrapper });
    expect(screen.getByText('Big Corp Deal')).toBeInTheDocument();
    expect(screen.getByText('Bob')).toBeInTheDocument();
  });

  it('shows Overdue badge when is_overdue is true', () => {
    const data = [
      {
        id: 'deal-2',
        name: 'Overdue Deal',
        value: 30000,
        stage_name: 'Proposal',
        owner_name: 'Carol',
        days_in_stage: 30,
        days_since_last_activity: 20,
        expected_close_date: '2024-01-15',
        is_overdue: true,
      },
    ];
    render(<StaleDealsList data={data} />, { wrapper: Wrapper });
    expect(screen.getByText('Overdue')).toBeInTheDocument();
  });

  it('shows Stale badge when inactive > 14 days', () => {
    const data = [
      {
        id: 'deal-3',
        name: 'Stale Deal',
        value: 20000,
        stage_name: 'Qualified',
        owner_name: 'Dave',
        days_in_stage: 20,
        days_since_last_activity: 18,
        expected_close_date: '2024-07-01',
        is_overdue: false,
      },
    ];
    render(<StaleDealsList data={data} />, { wrapper: Wrapper });
    expect(screen.getByText('Stale')).toBeInTheDocument();
  });

  it('shows Active badge when recent activity', () => {
    const data = [
      {
        id: 'deal-4',
        name: 'Active Deal',
        value: 10000,
        stage_name: 'New',
        owner_name: 'Eve',
        days_in_stage: 3,
        days_since_last_activity: 2,
        expected_close_date: '2024-08-01',
        is_overdue: false,
      },
    ];
    render(<StaleDealsList data={data} />, { wrapper: Wrapper });
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('renders card title', () => {
    render(<StaleDealsList data={[]} />, { wrapper: Wrapper });
    expect(screen.getByText('Deals Needing Attention')).toBeInTheDocument();
  });

  it('renders days formatted', () => {
    const data = [
      {
        id: 'deal-5',
        name: 'Format Test',
        value: 5000,
        stage_name: 'Lead',
        owner_name: 'Frank',
        days_in_stage: 7,
        days_since_last_activity: 14,
        expected_close_date: null,
        is_overdue: false,
      },
    ];
    render(<StaleDealsList data={data} />, { wrapper: Wrapper });
    expect(screen.getByText('7d')).toBeInTheDocument();
    expect(screen.getByText('14d ago')).toBeInTheDocument();
  });
});