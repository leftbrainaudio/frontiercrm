import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { Card } from '../ui/card';
import { formatCurrency } from './shared';

export interface PipelineValueChartProps {
  data: { date: string; value: number }[];
  loading?: boolean;
}

export function PipelineValueChart({ data, loading }: PipelineValueChartProps) {
  if (loading) {
    return (
      <Card title="Pipeline Value Over Time" padding="lg">
        <div className="h-[280px] animate-pulse bg-surface-tertiary dark:bg-dark-surface-tertiary rounded" />
      </Card>
    );
  }

  if (data.length === 0) {
    return (
      <Card title="Pipeline Value Over Time" padding="lg">
        <div className="flex h-[280px] items-center justify-center text-sm text-text-tertiary dark:text-dark-text-tertiary">
          No pipeline data for this period
        </div>
      </Card>
    );
  }

  return (
    <Card title="Pipeline Value Over Time" padding="lg">
      <div className="h-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 8, left: -8, bottom: 8 }}>
            <defs>
              <linearGradient id="pipelineGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--color-brand-500, #6366f1)" stopOpacity={0.3} />
                <stop offset="95%" stopColor="var(--color-brand-500, #6366f1)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" className="stroke-border dark:stroke-dark-border" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11 }}
              tickFormatter={(d: string) => {
                const parts = d.split('-');
                return `${parts[1]}/${parts[2]}`;
              }}
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
              formatter={(value: number) => [formatCurrency(value), 'Pipeline Value']}
              labelFormatter={(label: string) => new Date(label).toLocaleDateString('en-US', {
                month: 'short', day: 'numeric', year: 'numeric',
              })}
            />
            <Area
              type="monotone"
              dataKey="value"
              stroke="var(--color-brand-500, #6366f1)"
              strokeWidth={2}
              fill="url(#pipelineGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}