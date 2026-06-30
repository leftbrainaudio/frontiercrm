import { type ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';
import { cn } from '../../lib/utils';
import { Button } from '../atoms/button';

export interface ErrorStateProps {
  /** Title text */
  title?: string;
  /** Description text */
  description?: string;
  /** Error detail (shown in muted text, e.g. error code) */
  errorDetail?: string;
  /** Retry button callback */
  onRetry?: () => void;
  /** Custom icon */
  icon?: ReactNode;
  /** Additional className */
  className?: string;
}

export function ErrorState({
  title = 'Something went wrong',
  description = 'An unexpected error occurred. Please try again.',
  errorDetail,
  onRetry,
  icon,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-16 px-6 text-center',
        className,
      )}
      role="alert"
    >
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-50 dark:bg-red-900/30">
        <div className="text-red-500 dark:text-red-400">
          {icon ?? <AlertTriangle className="h-8 w-8" />}
        </div>
      </div>

      <h3 className="text-base font-semibold text-text-primary dark:text-dark-text-primary">
        {title}
      </h3>

      <p className="mt-1.5 max-w-sm text-sm text-text-secondary dark:text-dark-text-secondary">
        {description}
      </p>

      {errorDetail && (
        <p className="mt-2 text-xs text-text-tertiary dark:text-dark-text-tertiary font-mono">
          {errorDetail}
        </p>
      )}

      {onRetry && (
        <Button
          variant="secondary"
          size="md"
          className="mt-6"
          onClick={onRetry}
        >
          Try Again
        </Button>
      )}
    </div>
  );
}