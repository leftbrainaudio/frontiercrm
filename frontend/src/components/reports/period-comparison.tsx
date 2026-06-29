import { cn } from '../../lib/utils';
import { formatChange, isPositiveChange } from './shared';

export interface PeriodComparisonProps {
  label: string;
  currentValue: string;
  changeValue: number | null;
  isPercentage?: boolean;
}

export function PeriodComparison({ label, currentValue, changeValue, isPercentage = false }: PeriodComparisonProps) {
  const positive = isPositiveChange(changeValue);
  const changeStr = changeValue !== null
    ? `${positive ? '+' : ''}${changeValue.toFixed(isPercentage ? 1 : 0)}${isPercentage ? '%' : ''}`
    : null;

  return (
    <div className="flex items-center justify-between rounded-lg border border-border dark:border-dark-border px-4 py-3">
      <div className="space-y-0.5">
        <p className="text-xs font-medium text-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">
          {label}
        </p>
        <p className="text-lg font-bold text-text-primary dark:text-dark-text-primary">
          {currentValue}
        </p>
      </div>
      {changeStr && (
        <span
          className={cn(
            'inline-flex items-center gap-1 text-xs font-medium',
            positive
              ? 'text-emerald-600 dark:text-emerald-400'
              : 'text-red-600 dark:text-red-400',
          )}
        >
          <span>{positive ? '▲' : '▼'}</span>
          {changeStr}
        </span>
      )}
    </div>
  );
}