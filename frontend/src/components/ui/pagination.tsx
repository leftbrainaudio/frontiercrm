import { ChevronLeft, ChevronRight, MoreHorizontal } from 'lucide-react';
import { cn } from '../../lib/utils';

export interface PaginationProps {
  /** Total number of pages */
  pageCount: number;
  /** Current active page (1-indexed) */
  currentPage: number;
  /** Page change callback */
  onChange: (page: number) => void;
  /** Compact mode — shows fewer page buttons */
  compact?: boolean;
  /** Show/hide previous/next labels */
  showLabels?: boolean;
  /** Additional className */
  className?: string;
}

function getPageRange(
  current: number,
  total: number,
  compact: boolean,
): (number | 'ellipsis')[] {
  const siblings = compact ? 0 : 1;
  const totalVisible = compact ? 3 : 5; // siblings * 2 + 1

  if (total <= totalVisible + 2) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }

  const pages: (number | 'ellipsis')[] = [];

  const rangeStart = Math.max(2, current - siblings);
  const rangeEnd = Math.min(total - 1, current + siblings);

  // Always show page 1
  pages.push(1);

  if (rangeStart > 2) {
    pages.push('ellipsis');
  }

  for (let i = rangeStart; i <= rangeEnd; i++) {
    pages.push(i);
  }

  if (rangeEnd < total - 1) {
    pages.push('ellipsis');
  }

  if (total > 1) {
    pages.push(total);
  }

  return pages;
}

export function Pagination({
  pageCount,
  currentPage,
  onChange,
  compact = false,
  showLabels = false,
  className,
}: PaginationProps) {
  if (pageCount <= 1) return null;

  const pages = getPageRange(currentPage, pageCount, compact);

  const baseBtn =
    'inline-flex items-center justify-center rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900 disabled:opacity-40 disabled:pointer-events-none';

  const pageBtn = (isActive: boolean) =>
    cn(
      baseBtn,
      'h-8 min-w-[32px] px-2',
      isActive
        ? 'bg-brand-600 text-white dark:bg-brand-500'
        : 'text-text-secondary hover:bg-surface-secondary dark:text-dark-text-secondary dark:hover:bg-dark-surface-secondary',
    );

  const navBtn = cn(baseBtn, 'h-8 px-2.5 text-text-secondary hover:bg-surface-secondary dark:text-dark-text-secondary dark:hover:bg-dark-surface-secondary');

  return (
    <nav
      aria-label="Pagination"
      className={cn('flex items-center gap-1', className)}
    >
      {/* Previous */}
      <button
        type="button"
        className={navBtn}
        disabled={currentPage <= 1}
        onClick={() => onChange(currentPage - 1)}
        aria-label="Previous page"
      >
        <ChevronLeft className="h-4 w-4" />
        {showLabels && <span className="ml-1">Previous</span>}
      </button>

      {/* Page buttons */}
      {pages.map((page, i) =>
        page === 'ellipsis' ? (
          <span
            key={`ellipsis-${i}`}
            className="inline-flex h-8 w-8 items-center justify-center text-text-tertiary dark:text-dark-text-tertiary"
            aria-hidden="true"
          >
            <MoreHorizontal className="h-4 w-4" />
          </span>
        ) : (
          <button
            key={page}
            type="button"
            className={pageBtn(page === currentPage)}
            aria-current={page === currentPage ? 'page' : undefined}
            aria-label={`Page ${page}`}
            onClick={() => onChange(page)}
          >
            {page}
          </button>
        ),
      )}

      {/* Next */}
      <button
        type="button"
        className={navBtn}
        disabled={currentPage >= pageCount}
        onClick={() => onChange(currentPage + 1)}
        aria-label="Next page"
      >
        {showLabels && <span className="mr-1">Next</span>}
        <ChevronRight className="h-4 w-4" />
      </button>
    </nav>
  );
}