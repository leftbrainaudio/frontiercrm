import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Table } from '../../components/ui/table';

interface TestRow {
  id: string;
  name: string;
  age: number;
}

const columns = [
  { header: 'Name', accessor: 'name' as const, sortable: true },
  { header: 'Age', accessor: 'age' as const, sortable: true },
];

const data: TestRow[] = [
  { id: '1', name: 'Alice', age: 30 },
  { id: '2', name: 'Bob', age: 25 },
  { id: '3', name: 'Charlie', age: 35 },
];

describe('Table', () => {
  it('renders column headers', () => {
    render(<Table columns={columns} data={data} />);
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Age')).toBeInTheDocument();
  });

  it('renders data rows', () => {
    render(<Table columns={columns} data={data} />);
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('Bob')).toBeInTheDocument();
    expect(screen.getByText('Charlie')).toBeInTheDocument();
  });

  it('renders loading state with skeleton rows', () => {
    const { container } = render(<Table columns={columns} data={data} loading skeletonRows={3} />);
    const skeletonElements = container.querySelectorAll('[role="status"]');
    expect(skeletonElements.length).toBeGreaterThan(0);
  });

  it('renders empty content when no data', () => {
    render(<Table columns={columns} data={[]} />);
    expect(screen.getByText('No data available.')).toBeInTheDocument();
  });

  it('renders custom empty content', () => {
    render(<Table columns={columns} data={[]} emptyContent={<span>Nothing here</span>} />);
    expect(screen.getByText('Nothing here')).toBeInTheDocument();
  });

  it('supports sortable columns (click to sort)', async () => {
    const user = userEvent.setup();
    render(<Table columns={columns} data={data} />);
    const nameHeader = screen.getByText('Name');
    await user.click(nameHeader);
    const cells = screen.getAllByText(/Alice|Bob|Charlie/);
    expect(cells.length).toBe(3);
  });

  it('calls onSort when controlled sort is used', async () => {
    const onSort = vi.fn();
    const user = userEvent.setup();
    render(
      <Table
        columns={columns}
        data={data}
        sortColumn="Name"
        sortDirection="asc"
        onSort={onSort}
      />,
    );
    await user.click(screen.getByText('Name'));
    expect(onSort).toHaveBeenCalledWith('Name', 'desc');
  });

  it('shows sort indicator on active column', () => {
    render(
      <Table
        columns={columns}
        data={data}
        sortColumn="Name"
        sortDirection="asc"
      />,
    );
    const nameHeader = screen.getByText('Name').closest('th');
    expect(nameHeader).toHaveAttribute('aria-sort', 'ascending');
  });

  it('renders striped rows', () => {
    const { container } = render(<Table columns={columns} data={data} striped />);
    const rows = container.querySelectorAll('tbody tr');
    expect(rows.length).toBe(3);
  });

  it('renders bordered rows', () => {
    const { container } = render(<Table columns={columns} data={data} bordered />);
    const rows = container.querySelectorAll('tbody tr');
    expect(rows.length).toBe(3);
  });

  it('renders selectable rows with checkboxes', () => {
    render(
      <Table
        columns={columns}
        data={data}
        selectable
        rowKey={(r) => r.id}
        selectedKeys={new Set()}
        onSelectionChange={() => {}}
      />,
    );
    expect(screen.getByLabelText('Select all rows')).toBeInTheDocument();
    expect(screen.getByLabelText('Select row 1')).toBeInTheDocument();
  });

  it('calls onRowClick when a row is clicked', async () => {
    const onRowClick = vi.fn();
    const user = userEvent.setup();
    render(<Table columns={columns} data={data} onRowClick={onRowClick} />);
    await user.click(screen.getByText('Alice'));
    expect(onRowClick).toHaveBeenCalledTimes(1);
    expect(onRowClick).toHaveBeenCalledWith(
      expect.objectContaining({ id: '1', name: 'Alice' }),
    );
  });

  it('makes rows focusable when onRowClick is provided', () => {
    render(<Table columns={columns} data={data} onRowClick={vi.fn()} />);
    const rows = document.querySelectorAll('[role="button"]');
    expect(rows.length).toBe(3);
  });

  it('renders with custom cell renderer', () => {
    const customColumns = [
      {
        header: 'Name',
        accessor: 'name' as const,
        cell: (row: TestRow) => <strong>{row.name}</strong>,
      },
    ];
    render(<Table columns={customColumns} data={data} />);
    expect(screen.getByText('Alice').tagName).toBe('STRONG');
  });

  it('renders with accessor function', () => {
    const funcColumns = [
      {
        header: 'Label',
        accessor: (row: TestRow) => `${row.name} (${row.age})`,
      },
    ];
    render(<Table columns={funcColumns} data={data} />);
    expect(screen.getByText('Alice (30)')).toBeInTheDocument();
  });
});