import { type ReactNode } from 'react';
import { cn } from '../../lib/utils';
import { Skeleton } from '../atoms/skeleton';

export interface StatItem {
  label: string;
  value: string | number;
  trend?: string;
  trendUp?: boolean;
}

export interface StatCardProps {
  /** Title of the stat group */
  title?: string;
  /** Array of stat items to display */
  stats: StatItem[];
  /** Loading state */
  loading?: boolean;
  /** Number of columns for stat items */
  columns?: 2 | 3 | 4;
  /** Additional className */
  className?: string;
  /** Optional icon in header */
  icon?: ReactNode;
}

export function StatCard({
  title,
  stats,
  loading = false,
  columns = 3,
  className,
  icon,
}: StatCardProps) {
  const gridCols = {
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-4',
  };

  return (
    <div
      className={cn(
        'rounded-xl border border-border bg-white p-5 dark:border-dark-border dark:bg-dark-surface',
        className,
      )}
    >
      {(title || icon) && (
        <div className="flex items-center gap-2 mb-4">
          {icon && (
            <span className="text-text-secondary dark:text-dark-text-secondary">
              {icon}
            </span>
          )}
          {title && (
            <h3 className="text-sm font-semibold text-text-primary dark:text-dark-text-primary">
              {title}
            </h3>
          )}
        </div>
      )}

      {loading ? (
        <div className={cn('grid gap-4', gridCols[columns])}>
          {Array.from({ length: columns }).map((_, i) => (
            <div key={i} className="space-y-2">
              <Skeleton variant="text" width="70%" height={12} />
              <Skeleton variant="text" width="50%" height={24} />
            </div>
          ))}
        </div>
      ) : (
        <div className={cn('grid gap-4', gridCols[columns])}>
          {stats.map((stat, i) => (
            <div key={i}>
              <p className="text-xs font-medium text-text-secondary dark:text-dark-text-secondary truncate">
                {stat.label}
              </p>
              <p className="mt-1 text-lg font-semibold text-text-primary dark:text-dark-text-primary tabular-nums">
                {stat.value}
              </p>
              {stat.trend && (
                <p
                  className={cn(
                    'mt-0.5 text-xs font-medium',
                    stat.trendUp
                      ? 'text-emerald-600 dark:text-emerald-400'
                      : 'text-red-600 dark:text-red-400',
                  )}
                >
                  {stat.trend}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}