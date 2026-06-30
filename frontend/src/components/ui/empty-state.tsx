import { type ReactNode } from 'react';
import { Inbox } from 'lucide-react';
import { cn } from '../../lib/utils';
import { Button } from '../atoms/button';

export interface EmptyStateProps {
  /** Icon component or element */
  icon?: ReactNode;
  /** Title text */
  title: string;
  /** Description text */
  description?: string;
  /** Action button config */
  action?: {
    label: string;
    onClick: () => void;
  };
  /** Custom illustration slot (replaces default icon) */
  illustration?: ReactNode;
  /** Additional className */
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  illustration,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-16 px-6 text-center',
        className,
      )}
    >
      {illustration ? (
        <div className="mb-6">{illustration}</div>
      ) : (
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-surface-secondary dark:bg-dark-surface-secondary">
          <div className="text-text-tertiary dark:text-dark-text-tertiary">
            {icon ?? <Inbox className="h-8 w-8" />}
          </div>
        </div>
      )}

      <h3 className="text-base font-semibold text-text-primary dark:text-dark-text-primary">
        {title}
      </h3>

      {description && (
        <p className="mt-1.5 max-w-sm text-sm text-text-secondary dark:text-dark-text-secondary">
          {description}
        </p>
      )}

      {action && (
        <Button
          variant="primary"
          size="md"
          className="mt-6"
          onClick={action.onClick}
        >
          {action.label}
        </Button>
      )}
    </div>
  );
}