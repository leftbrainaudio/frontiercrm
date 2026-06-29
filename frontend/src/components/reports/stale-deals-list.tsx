import { useNavigate } from 'react-router-dom';
import { Table, type Column } from '../ui/table';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import { formatCurrency } from './shared';
import type { StaleDeal } from '../../types';

export interface StaleDealsListProps {
  data: StaleDeal[];
  loading?: boolean;
}

export function StaleDealsList({ data, loading }: StaleDealsListProps) {
  const navigate = useNavigate();

  const columns: Column<StaleDeal>[] = [
    { header: 'Deal', accessor: 'name', sortable: true },
    {
      header: 'Value',
      accessor: 'value',
      sortable: true,
      cell: (row) => formatCurrency(row.value),
    },
    { header: 'Stage', accessor: 'stage_name', sortable: true },
    { header: 'Rep', accessor: 'owner_name', sortable: true },
    {
      header: 'Days in Stage',
      accessor: 'days_in_stage',
      sortable: true,
      cell: (row) => `${row.days_in_stage}d`,
    },
    {
      header: 'Last Activity',
      accessor: 'days_since_last_activity',
      sortable: true,
      cell: (row) => `${row.days_since_last_activity}d ago`,
    },
    {
      header: 'Status',
      accessor: (row) => {
        if (row.is_overdue) return 'Overdue';
        if (row.days_since_last_activity > 14) return 'Stale';
        return 'Active';
      },
      cell: (row) => {
        if (row.is_overdue) return <Badge variant="danger">Overdue</Badge>;
        if (row.days_since_last_activity > 14) return <Badge variant="warning">Stale</Badge>;
        return <Badge variant="success">Active</Badge>;
      },
      sortable: true,
    },
  ];

  return (
    <Card title="Deals Needing Attention" padding="none">
      <Table
        columns={columns}
        data={data}
        loading={loading}
        skeletonRows={3}
        emptyContent="No stale deals found"
        onRowClick={(row) => navigate(`/pipeline/${row.id}`)}
      />
    </Card>
  );
}