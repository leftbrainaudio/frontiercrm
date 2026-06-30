import { Button } from '../atoms/button';
import { cn } from '../../lib/utils';

export interface SelectAllBannerProps {
  selectedOnPage: number;
  totalMatching: number;
  onSelectAll: () => void;
  onClear?: () => void;
  className?: string;
}

export function SelectAllBanner({
  selectedOnPage,
  totalMatching,
  onSelectAll,
  onClear,
  className,
}: SelectAllBannerProps) {
  return (
    <div
      className={cn(
        'flex items-center justify-between gap-4 border-t border-brand-200 bg-brand-50 px-4 py-3 dark:border-brand-800 dark:bg-brand-900/20',
        className,
      )}
      role="status"
      aria-live="polite"
    >
      <p className="text-sm text-brand-800 dark:text-brand-300">
        All <strong>{selectedOnPage}</strong> records on this page selected.{' '}
        <button
          type="button"
          onClick={onSelectAll}
          className="font-medium underline hover:no-underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
        >
          Select all <strong>{totalMatching.toLocaleString()}</strong> records matching this filter.
        </button>
      </p>
      {onClear && (
        <Button variant="ghost" size="sm" onClick={onClear}>
          Clear
        </Button>
      )}
    </div>
  );
}
