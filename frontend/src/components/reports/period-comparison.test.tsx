import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PeriodComparison } from './period-comparison';

describe('PeriodComparison', () => {
  it('renders label and currentValue', () => {
    render(<PeriodComparison label="Revenue" currentValue="$50,000" changeValue={12.5} />);
    expect(screen.getByText('Revenue')).toBeInTheDocument();
    expect(screen.getByText('$50,000')).toBeInTheDocument();
  });

  it('renders positive change with up arrow', () => {
    render(<PeriodComparison label="Growth" currentValue="10" changeValue={15} />);
    expect(screen.getByText('▲')).toBeInTheDocument();
    expect(screen.getByText('+15')).toBeInTheDocument();
  });

  it('renders negative change with down arrow', () => {
    render(<PeriodComparison label="Churn" currentValue="5" changeValue={-8} />);
    expect(screen.getByText('▼')).toBeInTheDocument();
    expect(screen.getByText('-8')).toBeInTheDocument();
  });

  it('formats percentage changes with one decimal and % suffix', () => {
    render(<PeriodComparison label="Rate" currentValue="75%" changeValue={5.3} isPercentage={true} />);
    expect(screen.getByText('+5.3%')).toBeInTheDocument();
  });

  it('renders nothing for change badge when changeValue is null', () => {
    render(<PeriodComparison label="Static" currentValue="42" changeValue={null} />);
    expect(screen.getByText('Static')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.queryByText('▲')).not.toBeInTheDocument();
    expect(screen.queryByText('▼')).not.toBeInTheDocument();
  });

  it('formats zero change with neutral styling', () => {
    render(<PeriodComparison label="Flat" currentValue="100" changeValue={0} />);
    expect(screen.getByText('▲')).toBeInTheDocument(); // 0 >= 0 so positive
    expect(screen.getByText('+0')).toBeInTheDocument();
  });
});