import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts';
import { Card } from '../molecules/card';
import { formatPercent } from './shared';

export interface WinRateChartProps {
  dealsByStage: { stage_name: string; count: number; value: number; probability: number }[];
  loading?: boolean;
}

export function WinRateChart({ dealsByStage, loading }: WinRateChartProps) {
  if (loading) {
    return (
      <Card title="Pipeline by Stage" padding="lg">
        <div className="h-[280px] animate-pulse bg-surface-tertiary dark:bg-dark-surface-tertiary rounded" />
      </Card>
    );
  }

  if (dealsByStage.length === 0) {
    return (
      <Card title="Pipeline by Stage" padding="lg">
        <div className="flex h-[280px] items-center justify-center text-sm text-text-tertiary dark:text-dark-text-tertiary">
          No stage data available
        </div>
      </Card>
    );
  }

  const chartData = dealsByStage.map((s) => ({
    name: s.stage_name,
    value: s.value,
    probability: s.probability,
    count: s.count,
  }));

  return (
    <Card title="Pipeline by Stage" padding="lg">
      <div className="h-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 8, right: 8, left: -8, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-border dark:stroke-dark-border" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 11 }}
              className="text-text-tertiary dark:text-dark-text-tertiary"
            />
            <YAxis
              tick={{ fontSize: 11 }}
              className="text-text-tertiary dark:text-dark-text-tertiary"
              tickFormatter={(v: number) =>
                v >= 1000000 ? `$${(v / 1000000).toFixed(1)}M` : v >= 1000 ? `$${(v / 1000).toFixed(0)}k` : `$${v}`
              }
            />
            <Tooltip
              contentStyle={{
                borderRadius: '8px',
                border: '1px solid var(--color-border)',
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                fontSize: '13px',
              }}
              formatter={(value: number, name: string) => {
                if (name === 'value') return [new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0 }).format(value), 'Value'];
                return [value, name];
              }}
            />
            <Bar
              dataKey="value"
              fill="var(--color-brand-500, #6366f1)"
              radius={[4, 4, 0, 0]}
              maxBarSize={48}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}