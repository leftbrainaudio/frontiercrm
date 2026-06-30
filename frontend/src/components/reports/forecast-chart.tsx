import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { Card } from '../molecules/card';
import { formatCurrency, ReportEmptyState } from './shared';
import type { MonthlyBreakdown } from '../../types';

interface ForecastChartProps {
  data?: MonthlyBreakdown[];
  loading?: boolean;
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: { value: number; payload: MonthlyBreakdown }[] }) {
  if (!active || !payload?.length) return null;
  const { month, expected_deals } = payload[0].payload;
  return (
    <div className="rounded-lg border border-border dark:border-dark-border bg-white dark:bg-dark-surface p-3 shadow-lg">
      <p className="text-sm font-medium text-text-primary dark:text-dark-text-primary">{month}</p>
      <p className="text-sm text-text-primary dark:text-dark-text-primary">{formatCurrency(payload[0].value)}</p>
      <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary">
        {expected_deals} deal{expected_deals !== 1 ? 's' : ''}
      </p>
    </div>
  );
}

export function ForecastChart({ data, loading }: ForecastChartProps) {
  if (loading) {
    return (
      <Card title="Monthly Forecast Breakdown" padding="lg">
        <div className="h-[280px] animate-pulse bg-surface-tertiary dark:bg-dark-surface-tertiary rounded" />
      </Card>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card title="Monthly Forecast Breakdown" padding="lg">
        <ReportEmptyState message="No monthly forecast data for this period" />
      </Card>
    );
  }

  return (
    <Card title="Monthly Forecast Breakdown" padding="lg">
      <div className="h-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: -8, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-border dark:stroke-dark-border" />
            <XAxis
              dataKey="month"
              tick={{ fontSize: 12, fill: 'currentColor' }}
              className="text-text-tertiary dark:text-dark-text-tertiary"
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tick={{ fontSize: 12, fill: 'currentColor' }}
              className="text-text-tertiary dark:text-dark-text-tertiary"
              tickLine={false}
              axisLine={false}
              tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar
              dataKey="projected_value"
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
