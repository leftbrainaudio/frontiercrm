import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TasksDueCard } from './tasks-due-card';

describe('TasksDueCard', () => {
  const defaultProps = {
    totalDue: 15,
    overdue: 3,
    dueToday: 5,
    byPriority: { urgent: 2, high: 4, medium: 6, low: 3 },
  };

  it('renders loading skeleton', () => {
    const { container } = render(<TasksDueCard {...defaultProps} loading={true} />);
    expect(screen.getByText('Tasks Summary')).toBeInTheDocument();
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('renders totalDue count prominently', () => {
    render(<TasksDueCard {...defaultProps} />);
    expect(screen.getByText('15')).toBeInTheDocument();
  });

  it('renders overdue count', () => {
    render(<TasksDueCard {...defaultProps} />);
    // The number "3" appears in both the overdue box and the "low" priority row
    // Scope by looking for it near "Overdue" text
    const overdueBox = screen.getByText('Overdue').closest('div');
    expect(overdueBox?.querySelector('.text-2xl')?.textContent).toBe('3');
  });

  it('renders dueToday count', () => {
    render(<TasksDueCard {...defaultProps} />);
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('renders "Overdue" label', () => {
    render(<TasksDueCard {...defaultProps} />);
    expect(screen.getByText('Overdue')).toBeInTheDocument();
  });

  it('renders "Due Today" label', () => {
    render(<TasksDueCard {...defaultProps} />);
    expect(screen.getByText('Due Today')).toBeInTheDocument();
  });

  it('renders priority entries with counts', () => {
    render(<TasksDueCard {...defaultProps} />);
    expect(screen.getByText('urgent')).toBeInTheDocument();
    expect(screen.getByText('high')).toBeInTheDocument();
    expect(screen.getByText('medium')).toBeInTheDocument();
    expect(screen.getByText('low')).toBeInTheDocument();
    // Counts should be rendered
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
    expect(screen.getByText('6')).toBeInTheDocument();
  });

  it('renders card title and subtitle', () => {
    render(<TasksDueCard {...defaultProps} />);
    expect(screen.getByText('Tasks Due')).toBeInTheDocument();
    expect(screen.getByText('Open tasks overview')).toBeInTheDocument();
  });

  it('renders "Total open" label', () => {
    render(<TasksDueCard {...defaultProps} />);
    expect(screen.getByText('Total open')).toBeInTheDocument();
  });

  it('handles empty byPriority gracefully', () => {
    render(<TasksDueCard {...defaultProps} byPriority={{}} />);
    expect(screen.getByText('15')).toBeInTheDocument();
  });
});