import { Table, type Column } from '../ui/table';
import { Card } from '../ui/card';

export interface DealVelocityTableProps {
  data: { stage_name: string; avg_days: number; deals_in_stage: number }[];
  loading?: boolean;
}

export function DealVelocityTable({ data, loading }: DealVelocityTableProps) {
  const columns: Column<{ stage_name: string; avg_days: number; deals_in_stage: number }>[] = [
    { header: 'Stage', accessor: 'stage_name', sortable: true },
    {
      header: 'Avg Days',
      accessor: 'avg_days',
      sortable: true,
      cell: (row) => `${row.avg_days.toFixed(1)}d`,
    },
    {
      header: 'Deals in Stage',
      accessor: 'deals_in_stage',
      sortable: true,
      width: '140px',
    },
    {
      header: 'Status',
      accessor: (row) => {
        if (row.deals_in_stage === 0) return '—';
        if (row.avg_days > 14) return '🔴 Slower';
        if (row.avg_days > 10) return '🟡 Slightly slower';
        if (row.avg_days > 7) return '🟢 Normal';
        return '🟢 Fast';
      },
      sortable: false,
      width: '140px',
    },
  ];

  return (
    <Card title="Average Time Per Stage" subtitle="Days deals spend in each stage" padding="none">
      <Table
        columns={columns}
        data={data}
        loading={loading}
        skeletonRows={4}
        emptyContent="No deal velocity data available"
      />
    </Card>
  );
}