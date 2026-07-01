import { type HTMLAttributes, type ReactNode } from 'react';
import { cn } from '../../lib/utils';

const variantStyles = {
  default: 'bg-white border border-border shadow-sm dark:bg-dark-surface dark:border-dark-border',
  elevated:
    'bg-white border border-border shadow-md dark:bg-dark-surface dark:border-dark-border dark:shadow-lg dark:shadow-black/10',
  outline: 'bg-transparent border border-border dark:border-dark-border',
  interactive:
    'bg-white border border-border shadow-sm hover:shadow-md hover:border-brand-300 cursor-pointer transition-all duration-200 dark:bg-dark-surface dark:border-dark-border dark:hover:border-brand-600 dark:hover:shadow-lg dark:hover:shadow-black/10',
} as const;

const paddingStyles = {
  none: '',
  sm: 'p-3',
  md: 'p-4 sm:p-5',
  lg: 'p-6 sm:p-8',
} as const;

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** Visual variant */
  variant?: keyof typeof variantStyles;
  /** Internal padding */
  padding?: keyof typeof paddingStyles;
  /** Optional header slot */
  header?: ReactNode;
  /** Optional footer slot */
  footer?: ReactNode;
  /** Title text for the card header */
  title?: string;
  /** Subtitle text shown below title */
  subtitle?: string;
}

export function Card({
  className,
  variant = 'default',
  padding = 'md',
  header,
  footer,
  title,
  subtitle,
  children,
  ...props
}: CardProps) {
  const showHeader = header || title;

  return (
    <div
      className={cn('rounded-lg', variantStyles[variant], className)}
      {...props}
    >
      {showHeader && (
        <div
          className={cn(
            'border-b border-border dark:border-dark-border',
            paddingStyles[padding],
            'pb-0',
          )}
        >
          <div className="pb-3">
            {header ?? (
              <>
                {title && (
                  <h3 className="text-base font-semibold text-text-primary dark:text-dark-text-primary">
                    {title}
                  </h3>
                )}
                {subtitle && (
                  <p className="mt-0.5 text-sm text-text-secondary dark:text-dark-text-secondary">
                    {subtitle}
                  </p>
                )}
              </>
            )}
          </div>
        </div>
      )}

      <div className={paddingStyles[padding]}>{children}</div>

      {footer && (
        <div
          className={cn(
            'border-t border-border dark:border-dark-border',
            paddingStyles[padding],
            'pt-0',
          )}
        >
          <div className="pt-3">{footer}</div>
        </div>
      )}
    </div>
  );
}