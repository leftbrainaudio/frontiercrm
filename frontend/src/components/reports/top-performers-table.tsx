import { Table, type Column } from '../ui/table';
import { Card } from '../molecules/card';
import { formatCurrency, formatPercent } from './shared';

export interface OwnerMetrics {
  owner_id: string;
  owner_name: string;
  pipeline_value: number;
  won_value: number;
  win_rate: number;
  active_deals: number;
  won_deals: number;
  lost_deals: number;
  avg_deal_value: number;
  activity_count: number;
}

export interface TopPerformersTableProps {
  data: OwnerMetrics[];
  loading?: boolean;
}

export function TopPerformersTable({ data, loading }: TopPerformersTableProps) {
  const columns: Column<OwnerMetrics>[] = [
    { header: 'Rep', accessor: 'owner_name', sortable: true },
    {
      header: 'Active Deals',
      accessor: 'active_deals',
      sortable: true,
      width: '120px',
    },
    {
      header: 'Pipeline Value',
      accessor: 'pipeline_value',
      sortable: true,
      cell: (row) => formatCurrency(row.pipeline_value),
    },
    {
      header: 'Won',
      accessor: 'won_value',
      sortable: true,
      cell: (row) => formatCurrency(row.won_value),
    },
    {
      header: 'Win Rate',
      accessor: 'win_rate',
      sortable: true,
      cell: (row) => formatPercent(row.win_rate),
    },
    {
      header: 'Avg Deal',
      accessor: 'avg_deal_value',
      sortable: true,
      cell: (row) => formatCurrency(row.avg_deal_value),
    },
    {
      header: 'Activities',
      accessor: 'activity_count',
      sortable: true,
      width: '100px',
    },
  ];

  return (
    <Card title="Rep Performance" subtitle="Per-owner breakdown" padding="none">
      <Table
        columns={columns}
        data={data}
        loading={loading}
        skeletonRows={3}
        emptyContent="No owner performance data available"
      />
    </Card>
  );
}