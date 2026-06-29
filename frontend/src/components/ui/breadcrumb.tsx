import { type ReactNode } from 'react';
import { ChevronRight, MoreHorizontal } from 'lucide-react';
import { cn } from '../../lib/utils';

export interface BreadcrumbItem {
  /** Item label */
  label: ReactNode;
  /** Optional href — last item is not a link */
  href?: string;
}

export interface BreadcrumbProps {
  /** Breadcrumb trail items */
  items: BreadcrumbItem[];
  /** Custom separator icon or element */
  separator?: ReactNode;
  /** Max items before collapsing into ellipsis */
  maxItems?: number;
  /** Additional className */
  className?: string;
}

export function Breadcrumb({
  items,
  separator,
  maxItems = 0,
  className,
}: BreadcrumbProps) {
  const shouldCollapse = maxItems > 0 && items.length > maxItems;

  let visibleItems: BreadcrumbItem[];
  let collapsed = false;

  if (shouldCollapse) {
    const first = items.slice(0, 1);
    const last = items.slice(-1);
    visibleItems = [...first, ...last];
    collapsed = true;
  } else {
    visibleItems = items;
  }

  const defaultSeparator = separator ?? (
    <ChevronRight className="h-3.5 w-3.5" />
  );

  return (
    <nav aria-label="Breadcrumb" className={cn('flex items-center', className)}>
      <ol className="flex items-center gap-1.5 text-sm">
        {visibleItems.map((item, i) => {
          const isLast = i === visibleItems.length - 1;

          return (
            <li key={i} className="flex items-center gap-1.5">
              {/* Collapsed indicator */}
              {collapsed && i === 1 && (
                <>
                  <span
                    className="flex items-center text-text-tertiary dark:text-dark-text-tertiary"
                    aria-hidden="true"
                  >
                    {defaultSeparator}
                  </span>
                  <span className="flex items-center text-text-tertiary dark:text-dark-text-tertiary">
                    <MoreHorizontal className="h-4 w-4" aria-label="More items" />
                  </span>
                </>
              )}

              {!isLast ? (
                <>
                  {item.href ? (
                    <a
                      href={item.href}
                      className="text-text-secondary hover:text-text-primary transition-colors dark:text-dark-text-secondary dark:hover:text-dark-text-primary"
                    >
                      {item.label}
                    </a>
                  ) : (
                    <span className="text-text-secondary dark:text-dark-text-secondary">
                      {item.label}
                    </span>
                  )}
                  <span
                    className="text-text-tertiary dark:text-dark-text-tertiary"
                    aria-hidden="true"
                  >
                    {defaultSeparator}
                  </span>
                </>
              ) : (
                <span
                  className="font-medium text-text-primary dark:text-dark-text-primary"
                  aria-current="page"
                >
                  {item.label}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}