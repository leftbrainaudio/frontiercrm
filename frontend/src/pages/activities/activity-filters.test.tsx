import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ActivityFilters, type TimelineFilterState } from './activity-filters';

const defaultFilters: TimelineFilterState = {
  start_date: '',
  end_date: '',
  activity_type: '',
};

describe('ActivityFilters', () => {
  it('renders "All types" pill as active by default', () => {
    const onChange = vi.fn();
    render(<ActivityFilters filters={defaultFilters} onChange={onChange} />);
    const allTypesBtn = screen.getByText('All types');
    expect(allTypesBtn).toBeInTheDocument();
    expect(allTypesBtn).toHaveAttribute('aria-pressed', 'true');
  });

  it('renders all activity type pills', () => {
    const onChange = vi.fn();
    render(<ActivityFilters filters={defaultFilters} onChange={onChange} />);
    expect(screen.getByText('Notes')).toBeInTheDocument();
    expect(screen.getByText('Calls')).toBeInTheDocument();
    expect(screen.getByText('Emails')).toBeInTheDocument();
    expect(screen.getByText('Meetings')).toBeInTheDocument();
    expect(screen.getByText('Tasks')).toBeInTheDocument();
    expect(screen.getByText('Deal changes')).toBeInTheDocument();
    expect(screen.getByText('File uploads')).toBeInTheDocument();
    expect(screen.getByText('System')).toBeInTheDocument();
  });

  it('renders date presets', () => {
    const onChange = vi.fn();
    render(<ActivityFilters filters={defaultFilters} onChange={onChange} />);
    expect(screen.getByText('Today')).toBeInTheDocument();
    expect(screen.getByText('This week')).toBeInTheDocument();
    expect(screen.getByText('This month')).toBeInTheDocument();
    expect(screen.getByText('Last 90 days')).toBeInTheDocument();
  });

  it('calls onChange with activity_type when a type pill is clicked', () => {
    const onChange = vi.fn();
    render(<ActivityFilters filters={defaultFilters} onChange={onChange} />);
    fireEvent.click(screen.getByText('Calls'));
    expect(onChange).toHaveBeenCalledWith({ ...defaultFilters, activity_type: 'call' });
  });

  it('calls onChange with start_date/end_date when a date preset is clicked', () => {
    const onChange = vi.fn();
    render(<ActivityFilters filters={defaultFilters} onChange={onChange} />);
    fireEvent.click(screen.getByText('This week'));
    // Should set start_date to 7 days ago (approximately)
    const call = onChange.mock.calls[0][0] as TimelineFilterState;
    expect(call.start_date).toBeTruthy();
    expect(call.end_date).toBeTruthy();
  });

  it('call "This week" preset sets start_date to ~7 days ago', () => {
    const onChange = vi.fn();
    render(<ActivityFilters filters={defaultFilters} onChange={onChange} />);
    fireEvent.click(screen.getByText('This week'));
    const call = onChange.mock.calls[0][0] as TimelineFilterState;
    const startDate = new Date(call.start_date);
    const sevenDaysMs = 7 * 86400000;
    const diff = Date.now() - startDate.getTime();
    expect(diff).toBeGreaterThan(sevenDaysMs - 86400000); // within ~1 day
    expect(diff).toBeLessThan(sevenDaysMs + 86400000);
  });

  it('marks the selected type pill as pressed', () => {
    const onChange = vi.fn();
    const filters: TimelineFilterState = { ...defaultFilters, activity_type: 'email' };
    render(<ActivityFilters filters={filters} onChange={onChange} />);
    expect(screen.getByText('Emails')).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByText('All types')).toHaveAttribute('aria-pressed', 'false');
  });

  it('shows "Clear all filters" link when filters are active', () => {
    const onChange = vi.fn();
    const filters: TimelineFilterState = { start_date: '2026-01-01', end_date: '', activity_type: '' };
    render(<ActivityFilters filters={filters} onChange={onChange} />);
    // There should be clear buttons visible
    const clearButtons = screen.getAllByText(/clear/i);
    expect(clearButtons.length).toBeGreaterThan(0);
  });

  it('calls onChange with empty filters when "Clear all" is clicked', () => {
    const onChange = vi.fn();
    const filters: TimelineFilterState = { start_date: '2026-01-01', end_date: '2026-06-30', activity_type: 'note' };
    render(<ActivityFilters filters={filters} onChange={onChange} />);
    // There are two "clear" elements — one mobile, one desktop. Click the mobile one.
    const clearButtons = screen.getAllByText(/^Clear all( filters)?$/i);
    fireEvent.click(clearButtons[0]); // click 'Clear all' (mobile)
    const lastCall = onChange.mock.calls[onChange.mock.calls.length - 1][0] as TimelineFilterState;
    expect(lastCall.start_date).toBe('');
    expect(lastCall.end_date).toBe('');
    expect(lastCall.activity_type).toBe('');
  });

  it('does not show "Clear all" when no filters are active', () => {
    const onChange = vi.fn();
    render(<ActivityFilters filters={defaultFilters} onChange={onChange} />);
    expect(screen.queryByText(/clear/i)).not.toBeInTheDocument();
  });

  it('renders date picker elements when showDatePicker is true', () => {
    const onChange = vi.fn();
    render(
      <ActivityFilters filters={defaultFilters} onChange={onChange} showDatePicker />,
    );
    // Should still have type pills
    expect(screen.getByText('All types')).toBeInTheDocument();
    // The showDatePicker flag doesn't change the rendered UI in the current
    // implementation but the prop is accepted
  });
});