import { type ReactNode } from 'react';
import { cn } from '../../lib/utils';

export interface PageBreadcrumb {
  label: string;
  href?: string;
}

export interface PageHeaderProps {
  /** Page title */
  title: string;
  /** Optional description */
  description?: string;
  /** Optional breadcrumbs */
  breadcrumbs?: PageBreadcrumb[];
  /** Actions shown on the right side */
  actions?: ReactNode;
  /** Additional className */
  className?: string;
}

export function PageHeader({
  title,
  description,
  breadcrumbs,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <div className={cn('flex flex-col gap-1', className)}>
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav className="flex items-center gap-1.5 text-xs text-text-tertiary dark:text-dark-text-tertiary mb-1" aria-label="Breadcrumb">
          {breadcrumbs.map((crumb, i) => (
            <span key={i} className="flex items-center gap-1.5">
              {i > 0 && <span aria-hidden="true">/</span>}
              {crumb.href ? (
                <a
                  href={crumb.href}
                  className="hover:text-text-primary dark:hover:text-dark-text-primary transition-colors"
                >
                  {crumb.label}
                </a>
              ) : (
                <span className="text-text-secondary dark:text-dark-text-secondary font-medium">
                  {crumb.label}
                </span>
              )}
            </span>
          ))}
        </nav>
      )}

      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <h1 className="text-xl font-semibold text-text-primary dark:text-dark-text-primary sm:text-2xl">
            {title}
          </h1>
          {description && (
            <p className="mt-1 text-sm text-text-secondary dark:text-dark-text-secondary">
              {description}
            </p>
          )}
        </div>
        {actions && (
          <div className="flex items-center gap-2 shrink-0">
            {actions}
          </div>
        )}
      </div>
    </div>
  );
}