import { Card } from '../ui/card';
import { formatPercent } from './shared';

export interface StageFunnelProps {
  data: { from_stage: string; to_stage: string; conversion_rate: number; deals_entered: number; deals_converted: number }[];
  loading?: boolean;
}

export function StageFunnel({ data, loading }: StageFunnelProps) {
  if (loading) {
    return (
      <Card title="Stage Conversion Funnel" padding="lg">
        <div className="h-[280px] animate-pulse bg-surface-tertiary dark:bg-dark-surface-tertiary rounded" />
      </Card>
    );
  }

  if (data.length === 0) {
    return (
      <Card title="Stage Conversion Funnel" padding="lg">
        <div className="flex h-[280px] items-center justify-center text-sm text-text-tertiary dark:text-dark-text-tertiary">
          No conversion data available
        </div>
      </Card>
    );
  }

  const maxDeals = Math.max(...data.map((d) => d.deals_entered), 1);

  return (
    <Card title="Stage Conversion Funnel" padding="lg">
      <div className="space-y-0">
        {data.map((item, i) => {
          const widthPct = (item.deals_entered / maxDeals) * 100;
          return (
            <div key={`${item.from_stage}-${item.to_stage}`} className="flex flex-col items-center">
              {/* From stage */}
              <div className="flex w-full items-center justify-between py-2">
                <span className="text-xs font-medium text-text-primary dark:text-dark-text-primary">
                  {item.from_stage}
                </span>
                <span className="text-xs text-text-secondary dark:text-dark-text-secondary">
                  {item.deals_entered} deals
                </span>
              </div>

              {/* Funnel bar */}
              <div className="flex w-full justify-center">
                <div
                  className="h-6 rounded bg-brand-500 dark:bg-brand-600 flex items-center justify-center text-xs text-white font-medium transition-all"
                  style={{ width: `${Math.max(widthPct, 10)}%` }}
                >
                  {formatPercent(item.conversion_rate)}
                </div>
              </div>

              {/* Arrow down */}
              {i < data.length - 1 && (
                <div className="flex justify-center py-1">
                  <span className="text-xs text-text-tertiary dark:text-dark-text-tertiary">↓</span>
                </div>
              )}

              {/* Last stage - show to_stage */}
              {i === data.length - 1 && (
                <div className="flex w-full items-center justify-between py-2">
                  <span className="text-xs font-medium text-text-primary dark:text-dark-text-primary">
                    {item.to_stage}
                  </span>
                  <span className="text-xs text-text-secondary dark:text-dark-text-secondary">
                    {item.deals_converted} deals
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}