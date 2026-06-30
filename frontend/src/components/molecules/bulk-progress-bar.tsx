import { cn } from '../../lib/utils';
import { Spinner } from '../ui/spinner';
import { CheckCircle, AlertCircle, XCircle } from 'lucide-react';
import type { BulkJobStatus } from '../../types';

export interface BulkProgressBarProps {
  processed: number;
  total: number;
  status: BulkJobStatus;
  showLabel?: boolean;
  className?: string;
}

const STATUS_ICONS: Record<BulkJobStatus, React.ReactNode | null> = {
  pending: null,
  running: null,
  completed: <CheckCircle className="h-4 w-4 text-emerald-500" />,
  failed: <XCircle className="h-4 w-4 text-red-500" />,
  partial: <AlertCircle className="h-4 w-4 text-amber-500" />,
};

const STATUS_LABELS: Record<BulkJobStatus, string> = {
  pending: 'Waiting to start…',
  running: 'In progress…',
  completed: 'Completed',
  failed: 'Failed',
  partial: 'Completed with errors',
};

export function BulkProgressBar({
  processed,
  total,
  status,
  showLabel = true,
  className,
}: BulkProgressBarProps) {
  const pct = total > 0 ? Math.round((processed / total) * 100) : 0;
  const isRunning = status === 'pending' || status === 'running';

  return (
    <div className={cn('flex items-center gap-3', className)}>
      {isRunning ? (
        <Spinner size="sm" />
      ) : (
        STATUS_ICONS[status]
      )}

      <div className="flex-1 min-w-0">
        {/* Bar */}
        <div className="h-2 w-full overflow-hidden rounded-full bg-surface-secondary dark:bg-dark-surface-secondary">
          <div
            className={cn(
              'h-full rounded-full transition-all duration-500',
              status === 'failed' && 'bg-red-500',
              status === 'partial' && 'bg-amber-500',
              isRunning && 'bg-brand-500',
              (status === 'completed' || status === 'pending') && 'bg-brand-500',
            )}
            style={{ width: `${pct}%` }}
          />
        </div>

        {/* Label */}
        {showLabel && (
          <p className="mt-1 text-xs text-text-secondary dark:text-dark-text-secondary">
            {isRunning ? `${processed}/${total} (${pct}%)` : STATUS_LABELS[status]}
          </p>
        )}
      </div>

      {!isRunning && showLabel && (
        <span className="shrink-0 text-xs font-medium text-text-secondary dark:text-dark-text-secondary">
          {processed}/{total}
        </span>
      )}
    </div>
  );
}
