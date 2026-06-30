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
import { CHART_COLORS } from './shared';

export interface ActivityMetricsChartProps {
  byType: { activity_type: string; label: string; count: number }[];
  byDay: { date: string; count: number }[];
  total: number;
  callsAvgDuration?: number;
  loading?: boolean;
}

export function ActivityMetricsChart({ byType, byDay, total, callsAvgDuration, loading }: ActivityMetricsChartProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Activity Volume by Type" padding="lg">
          <div className="h-[240px] animate-pulse bg-surface-tertiary dark:bg-dark-surface-tertiary rounded" />
        </Card>
        <Card title="Activity Volume by Day" padding="lg">
          <div className="h-[240px] animate-pulse bg-surface-tertiary dark:bg-dark-surface-tertiary rounded" />
        </Card>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      {/* By Type — horizontal bar */}
      <Card title="Activity Volume by Type" subtitle={`Total: ${total}${callsAvgDuration ? ` · Avg call: ${callsAvgDuration}m` : ''}`} padding="lg">
        {byType.length === 0 ? (
          <div className="flex h-[240px] items-center justify-center text-sm text-text-tertiary dark:text-dark-text-tertiary">
            No activities in this period
          </div>
        ) : (
          <div className="space-y-3">
            {byType.map((item, i) => {
              const maxCount = Math.max(...byType.map((t) => t.count));
              const pct = maxCount > 0 ? (item.count / maxCount) * 100 : 0;
              return (
                <div key={item.activity_type} className="flex items-center gap-3">
                  <span className="w-20 text-xs text-text-secondary dark:text-dark-text-secondary truncate text-right">
                    {item.label}
                  </span>
                  <div className="flex-1 h-6 rounded bg-surface-secondary dark:bg-dark-surface-secondary overflow-hidden">
                    <div
                      className="h-full rounded transition-all duration-500"
                      style={{
                        width: `${Math.max(pct, 3)}%`,
                        backgroundColor: CHART_COLORS[i % CHART_COLORS.length],
                      }}
                    />
                  </div>
                  <span className="w-12 text-xs font-medium text-text-primary dark:text-dark-text-primary text-right">
                    {item.count}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      {/* By Day — bar chart */}
      <Card title="Activity Volume by Day" padding="lg">
        {byDay.length === 0 ? (
          <div className="flex h-[240px] items-center justify-center text-sm text-text-tertiary dark:text-dark-text-tertiary">
            No activity data by day
          </div>
        ) : (
          <div className="h-[240px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={byDay} margin={{ top: 8, right: 8, left: -8, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border dark:stroke-dark-border" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 10 }}
                  tickFormatter={(d: string) => {
                    const parts = d.split('-');
                    return `${parts[1]}/${parts[2]}`;
                  }}
                  className="text-text-tertiary dark:text-dark-text-tertiary"
                />
                <YAxis
                  tick={{ fontSize: 11 }}
                  className="text-text-tertiary dark:text-dark-text-tertiary"
                  allowDecimals={false}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: '8px',
                    border: '1px solid var(--color-border)',
                    fontSize: '13px',
                  }}
                  labelFormatter={(label: string) => new Date(label).toLocaleDateString('en-US', {
                    month: 'short', day: 'numeric',
                  })}
                />
                <Bar
                  dataKey="count"
                  fill={CHART_COLORS[4]}
                  radius={[2, 2, 0, 0]}
                  maxBarSize={16}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </Card>
    </div>
  );
}