import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  MetricCardSmall,
  ReportEmptyState,
  ReportLoading,
  formatCurrency,
  formatPercent,
  formatChange,
  formatChangeAbsolute,
  isPositiveChange,
  CHART_COLORS,
} from './shared';

describe('formatCurrency', () => {
  it('formats whole numbers', () => {
    expect(formatCurrency(50000)).toBe('$50,000');
  });

  it('formats zero', () => {
    expect(formatCurrency(0)).toBe('$0');
  });

  it('formats small numbers', () => {
    expect(formatCurrency(99)).toBe('$99');
  });

  it('formats large numbers', () => {
    expect(formatCurrency(1234567)).toBe('$1,234,567');
  });
});

describe('formatPercent', () => {
  it('converts decimal to percentage string', () => {
    expect(formatPercent(0.6)).toBe('60%');
  });

  it('handles zero', () => {
    expect(formatPercent(0)).toBe('0%');
  });

  it('handles whole number', () => {
    expect(formatPercent(1)).toBe('100%');
  });

  it('rounds to nearest integer', () => {
    expect(formatPercent(0.456)).toBe('46%');
  });
});

describe('formatChange', () => {
  it('prefixes positive values with +', () => {
    expect(formatChange(12.5)).toBe('+12.5%');
  });

  it('prefixes negative values with -', () => {
    expect(formatChange(-5.3)).toBe('-5.3%');
  });

  it('returns — for null', () => {
    expect(formatChange(null)).toBe('—');
  });

  it('handles zero', () => {
    expect(formatChange(0)).toBe('+0.0%');
  });
});

describe('formatChangeAbsolute', () => {
  it('prefixes positive values with +', () => {
    expect(formatChangeAbsolute(5)).toBe('+5');
  });

  it('prefixes negative values with -', () => {
    expect(formatChangeAbsolute(-3)).toBe('-3');
  });

  it('returns — for null', () => {
    expect(formatChangeAbsolute(null)).toBe('—');
  });
});

describe('isPositiveChange', () => {
  it('returns true for positive values', () => {
    expect(isPositiveChange(10)).toBe(true);
  });

  it('returns true for zero', () => {
    expect(isPositiveChange(0)).toBe(true);
  });

  it('returns false for negative values', () => {
    expect(isPositiveChange(-1)).toBe(false);
  });

  it('returns true for null', () => {
    expect(isPositiveChange(null)).toBe(true);
  });
});

describe('CHART_COLORS', () => {
  it('has 8 color values', () => {
    expect(CHART_COLORS).toHaveLength(8);
  });

  it('all values are valid hex colors', () => {
    CHART_COLORS.forEach((color) => {
      expect(color).toMatch(/^#[0-9a-f]{6}$/);
    });
  });
});

describe('MetricCardSmall', () => {
  it('renders title and value', () => {
    render(
      <MetricCardSmall
        title="Revenue"
        value="$100k"
        change={null}
        positive={true}
        icon={<span data-testid="icon">$</span>}
      />,
    );
    expect(screen.getByText('Revenue')).toBeInTheDocument();
    expect(screen.getByText('$100k')).toBeInTheDocument();
  });

  it('renders change indicator when provided', () => {
    render(
      <MetricCardSmall
        title="Growth"
        value="20%"
        change="+5%"
        positive={true}
        icon={<span data-testid="icon">%</span>}
      />,
    );
    expect(screen.getByText('+5%')).toBeInTheDocument();
    expect(screen.getByText('▲')).toBeInTheDocument();
  });

  it('renders negative change with down arrow', () => {
    render(
      <MetricCardSmall
        title="Loss"
        value="-10%"
        change="-3%"
        positive={false}
        icon={<span data-testid="icon">x</span>}
      />,
    );
    expect(screen.getByText('▼')).toBeInTheDocument();
    expect(screen.getByText('-3%')).toBeInTheDocument();
  });

  it('renders icon', () => {
    render(
      <MetricCardSmall
        title="Count"
        value="42"
        change={null}
        positive={true}
        icon={<span data-testid="icon">#</span>}
      />,
    );
    expect(screen.getByTestId('icon')).toBeInTheDocument();
  });

  it('does not render change section when change is null', () => {
    render(
      <MetricCardSmall
        title="Static"
        value="100"
        change={null}
        positive={true}
        icon={<span data-testid="icon">s</span>}
      />,
    );
    expect(screen.queryByText('▲')).not.toBeInTheDocument();
    expect(screen.queryByText('▼')).not.toBeInTheDocument();
  });
});

describe('ReportEmptyState', () => {
  it('renders the message', () => {
    render(<ReportEmptyState message="No data available" />);
    expect(screen.getByText('No data available')).toBeInTheDocument();
  });
});

describe('ReportLoading', () => {
  it('renders the specified number of rows', () => {
    const { container } = render(<ReportLoading rows={3} />);
    const rows = container.querySelectorAll('.h-4');
    expect(rows.length).toBe(3);
  });

  it('defaults to 3 rows', () => {
    const { container } = render(<ReportLoading />);
    const rows = container.querySelectorAll('.h-4');
    expect(rows.length).toBe(3);
  });
});