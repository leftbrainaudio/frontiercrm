import { type ReactNode } from 'react';
import { cn } from '../../lib/utils';
import { Card } from './card';
import { Skeleton } from '../atoms/skeleton';

export interface MetricCardProps {
  /** Metric label */
  label: string;
  /** Metric value */
  value: string | number;
  /** Optional icon */
  icon?: ReactNode;
  /** Optional trend indicator (e.g. "+12%") */
  trend?: string;
  /** Whether the trend is positive (green) or negative (red) */
  trendUp?: boolean;
  /** Loading state */
  loading?: boolean;
  /** Optional subtitle / description */
  subtitle?: string;
  /** Additional className */
  className?: string;
}

export function MetricCard({
  label,
  value,
  icon,
  trend,
  trendUp = true,
  loading = false,
  subtitle,
  className,
}: MetricCardProps) {
  if (loading) {
    return (
      <Card className={className}>
        <div className="space-y-3">
          <Skeleton variant="text" width="60%" height={14} />
          <Skeleton variant="text" width="40%" height={28} />
          <Skeleton variant="text" width="30%" height={12} />
        </div>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-text-secondary dark:text-dark-text-secondary truncate">
            {label}
          </p>
          <p className="mt-1 text-2xl font-semibold text-text-primary dark:text-dark-text-primary tabular-nums">
            {value}
          </p>
          {subtitle && (
            <p className="mt-0.5 text-xs text-text-tertiary dark:text-dark-text-tertiary">
              {subtitle}
            </p>
          )}
          {trend && (
            <p
              className={cn(
                'mt-1 text-xs font-medium',
                trendUp
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : 'text-red-600 dark:text-red-400',
              )}
            >
              {trend}
            </p>
          )}
        </div>
        {icon && (
          <div className="shrink-0 ml-3 rounded-lg bg-surface-secondary p-2.5 text-text-secondary dark:bg-dark-surface-secondary dark:text-dark-text-secondary">
            {icon}
          </div>
        )}
      </div>
    </Card>
  );
}