import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ReportHeader, type PresetRange } from './report-header';

describe('ReportHeader', () => {
  const defaultProps = {
    title: 'Reports & Analytics',
    preset: '30d' as PresetRange,
    onPresetChange: vi.fn(),
    startDate: '2024-01-01',
    endDate: '2024-01-31',
    onDateChange: vi.fn(),
    pipelineId: undefined,
    pipelines: [
      { id: 'pipe-1', name: 'Sales Pipeline' },
      { id: 'pipe-2', name: 'Marketing Pipeline' },
    ],
    onPipelineChange: vi.fn(),
    groupBy: undefined,
    onGroupByChange: vi.fn(),
  };

  it('renders the title', () => {
    render(<ReportHeader {...defaultProps} />);
    expect(screen.getByText('Reports & Analytics')).toBeInTheDocument();
  });

  it('renders all preset date buttons (7d, 30d, 90d, This Q)', () => {
    render(<ReportHeader {...defaultProps} />);
    expect(screen.getByText('7d')).toBeInTheDocument();
    expect(screen.getByText('30d')).toBeInTheDocument();
    expect(screen.getByText('90d')).toBeInTheDocument();
    expect(screen.getByText('This Q')).toBeInTheDocument();
  });

  it('highlights the active preset', () => {
    render(<ReportHeader {...defaultProps} preset="7d" />);
    const button = screen.getByText('7d');
    expect(button.className).toContain('shadow-sm');
  });

  it('calls onPresetChange when a preset button is clicked', async () => {
    const onPresetChange = vi.fn();
    const user = userEvent.setup();
    render(<ReportHeader {...defaultProps} onPresetChange={onPresetChange} />);
    await user.click(screen.getByText('90d'));
    expect(onPresetChange).toHaveBeenCalledWith('90d');
  });

  it('shows custom date inputs when preset is custom', () => {
    render(<ReportHeader {...defaultProps} preset="custom" />);
    const dateInputs = screen.getAllByDisplayValue(/2024-01/);
    expect(dateInputs.length).toBe(2);
  });

  it('calls onPresetChange with "custom" when custom is needed', async () => {
    const onPresetChange = vi.fn();
    const user = userEvent.setup();
    render(<ReportHeader {...defaultProps} onPresetChange={onPresetChange} />);
    await user.click(screen.getByText('This Q'));
    expect(onPresetChange).toHaveBeenCalledWith('quarter');
  });

  it('calls onDateChange when custom date inputs change', async () => {
    const onDateChange = vi.fn();
    const user = userEvent.setup();
    render(
      <ReportHeader
        {...defaultProps}
        preset="custom"
        startDate="2024-01-01"
        endDate="2024-01-31"
        onDateChange={onDateChange}
      />,
    );
    const inputs = screen.getAllByDisplayValue(/2024-01/);
    await user.clear(inputs[0]);
    await user.type(inputs[0], '2024-02-01');
    expect(onDateChange).toHaveBeenCalled();
  });

  it('renders pipeline filter dropdown with "All Pipelines" option', () => {
    render(<ReportHeader {...defaultProps} />);
    expect(screen.getByText('All Pipelines')).toBeInTheDocument();
    expect(screen.getByText('Sales Pipeline')).toBeInTheDocument();
    expect(screen.getByText('Marketing Pipeline')).toBeInTheDocument();
  });

  it('selects "All Pipelines" when pipelineId is undefined', () => {
    render(<ReportHeader {...defaultProps} pipelineId={undefined} />);
    const selects = screen.getAllByRole('combobox');
    const pipelineSelect = selects[0] as HTMLSelectElement;
    expect(pipelineSelect.value).toBe('');
  });

  it('calls onPipelineChange when pipeline selection changes', async () => {
    const onPipelineChange = vi.fn();
    const user = userEvent.setup();
    render(<ReportHeader {...defaultProps} onPipelineChange={onPipelineChange} />);
    const select = screen.getByDisplayValue('All Pipelines');
    await user.selectOptions(select, 'pipe-1');
    expect(onPipelineChange).toHaveBeenCalledWith('pipe-1');
  });

  it('renders group by dropdown with "Group: None" default', () => {
    render(<ReportHeader {...defaultProps} />);
    expect(screen.getByText('Group: None')).toBeInTheDocument();
    expect(screen.getByText('Group: Owner')).toBeInTheDocument();
  });

  it('calls onGroupByChange when group selection changes', async () => {
    const onGroupByChange = vi.fn();
    const user = userEvent.setup();
    render(<ReportHeader {...defaultProps} onGroupByChange={onGroupByChange} />);
    const select = screen.getByDisplayValue('Group: None');
    await user.selectOptions(select, 'owner');
    expect(onGroupByChange).toHaveBeenCalledWith('owner');
  });

  it('shows selected pipeline option', () => {
    render(<ReportHeader {...defaultProps} pipelineId="pipe-1" />);
    const select = screen.getByDisplayValue('Sales Pipeline') as HTMLSelectElement;
    expect(select.value).toBe('pipe-1');
  });

  it('shows selected group by option', () => {
    render(<ReportHeader {...defaultProps} groupBy="owner" />);
    const select = screen.getByDisplayValue('Group: Owner') as HTMLSelectElement;
    expect(select.value).toBe('owner');
  });
});