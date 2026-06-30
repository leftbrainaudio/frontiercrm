import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PipelineValueChart } from './pipeline-value-chart';
import { WinRateChart } from './win-rate-chart';
import { ActivityMetricsChart } from './activity-metrics-chart';

// Mock recharts to render simple div wrappers in jsdom
vi.mock('recharts', () => {
  const MockResponsiveContainer = ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  );
  const MockAreaChart = ({ children }: { children: React.ReactNode }) => (
    <div data-testid="area-chart">{children}</div>
  );
  const MockBarChart = ({ children }: { children: React.ReactNode }) => (
    <div data-testid="bar-chart">{children}</div>
  );
  return {
    ResponsiveContainer: MockResponsiveContainer,
    AreaChart: MockAreaChart,
    Area: () => <div data-testid="area" />,
    BarChart: MockBarChart,
    Bar: () => <div data-testid="bar" />,
    XAxis: () => <div data-testid="xaxis" />,
    YAxis: () => <div data-testid="yaxis" />,
    Tooltip: () => <div data-testid="tooltip" />,
    CartesianGrid: () => <div data-testid="cartesian-grid" />,
    Legend: () => <div data-testid="legend" />,
  };
});

describe('PipelineValueChart', () => {
  it('renders loading skeleton', () => {
    const { container } = render(<PipelineValueChart data={[]} loading={true} />);
    expect(screen.getByText('Pipeline Value Over Time')).toBeInTheDocument();
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('renders empty state when no data', () => {
    render(<PipelineValueChart data={[]} />);
    expect(screen.getByText('No pipeline data for this period')).toBeInTheDocument();
  });

  it('renders chart when data provided', () => {
    const data = [
      { date: '2024-01-01', value: 10000 },
      { date: '2024-01-02', value: 15000 },
    ];
    render(<PipelineValueChart data={data} />);
    expect(screen.getByText('Pipeline Value Over Time')).toBeInTheDocument();
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
  });
});

describe('WinRateChart', () => {
  it('renders loading skeleton', () => {
    const { container } = render(<WinRateChart dealsByStage={[]} loading={true} />);
    expect(screen.getByText('Pipeline by Stage')).toBeInTheDocument();
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('renders empty state when no data', () => {
    render(<WinRateChart dealsByStage={[]} />);
    expect(screen.getByText('No stage data available')).toBeInTheDocument();
  });

  it('renders the mapped stage data in chart wrapper', () => {
    const data = [
      { stage_name: 'Qualified', count: 5, value: 50000, probability: 0.3 },
      { stage_name: 'Proposal', count: 3, value: 100000, probability: 0.6 },
    ];
    render(<WinRateChart dealsByStage={data} />);
    expect(screen.getByText('Pipeline by Stage')).toBeInTheDocument();
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
  });
});

describe('ActivityMetricsChart', () => {
  const defaultProps = {
    byType: [],
    byDay: [],
    total: 0,
  };

  it('renders loading state', () => {
    const { container } = render(<ActivityMetricsChart {...defaultProps} loading={true} />);
    expect(screen.getByText('Activity Volume by Type')).toBeInTheDocument();
    expect(screen.getByText('Activity Volume by Day')).toBeInTheDocument();
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('renders empty state when no data', () => {
    render(<ActivityMetricsChart {...defaultProps} />);
    expect(screen.getByText('No activities in this period')).toBeInTheDocument();
    expect(screen.getByText('No activity data by day')).toBeInTheDocument();
  });

  it('renders activity type bars', () => {
    const props = {
      ...defaultProps,
      byType: [
        { activity_type: 'call', label: 'Calls', count: 12 },
        { activity_type: 'email', label: 'Emails', count: 25 },
      ],
      total: 37,
    };
    render(<ActivityMetricsChart {...props} />);
    expect(screen.getByText('Calls')).toBeInTheDocument();
    expect(screen.getByText('Emails')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('25')).toBeInTheDocument();
  });

  it('shows call average duration when provided', () => {
    render(<ActivityMetricsChart {...defaultProps} callsAvgDuration={15} />);
    expect(screen.getByText(/Avg call: 15m/)).toBeInTheDocument();
  });

  it('shows total in subtitle', () => {
    render(<ActivityMetricsChart {...defaultProps} total={42} />);
    expect(screen.getByText(/Total: 42/)).toBeInTheDocument();
  });
});