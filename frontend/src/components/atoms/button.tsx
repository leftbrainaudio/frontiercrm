import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';

const variantStyles = {
  primary:
    'bg-brand-600 text-white hover:bg-brand-700 focus-visible:ring-brand-500 shadow-sm dark:bg-brand-500 dark:hover:bg-brand-600',
  secondary:
    'bg-surface-secondary text-text-primary hover:bg-surface-tertiary border border-border focus-visible:ring-brand-500 shadow-sm dark:bg-dark-surface-secondary dark:text-dark-text-primary dark:hover:bg-dark-surface-tertiary dark:border-dark-border',
  outline:
    'bg-transparent text-text-primary border-2 border-border hover:bg-surface-secondary hover:border-brand-500 focus-visible:ring-brand-500 dark:text-dark-text-primary dark:border-dark-border dark:hover:bg-dark-surface-secondary',
  ghost:
    'bg-transparent text-text-primary hover:bg-surface-secondary focus-visible:ring-brand-500 dark:text-dark-text-primary dark:hover:bg-dark-surface-secondary',
  danger:
    'bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500 shadow-sm dark:bg-red-500 dark:hover:bg-red-600',
} as const;

const sizeStyles = {
  sm: 'h-8 px-3 text-xs gap-1.5',
  md: 'h-10 px-4 text-sm gap-2',
  lg: 'h-12 px-6 text-base gap-2.5',
} as const;

const spinnerSizes = {
  sm: 'h-3.5 w-3.5',
  md: 'h-4 w-4',
  lg: 'h-5 w-5',
} as const;

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual variant */
  variant?: keyof typeof variantStyles;
  /** Size */
  size?: keyof typeof sizeStyles;
  /** Show loading spinner and disable interaction */
  loading?: boolean;
  /** Take full width of parent */
  fullWidth?: boolean;
  /** Icon to show before children */
  icon?: ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      loading = false,
      fullWidth = false,
      disabled,
      icon,
      children,
      type = 'button',
      ...props
    },
    ref,
  ) => {
    const isDisabled = disabled || loading;

    return (
      <button
        ref={ref}
        type={type}
        disabled={isDisabled}
        className={cn(
          'inline-flex items-center justify-center rounded-lg font-medium transition-all duration-150',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900',
          'disabled:pointer-events-none disabled:opacity-50',
          variantStyles[variant],
          sizeStyles[size],
          fullWidth && 'w-full',
          className,
        )}
        aria-busy={loading || undefined}
        {...props}
      >
        {loading ? (
          <Loader2
            className={cn('animate-spin', spinnerSizes[size])}
            aria-hidden="true"
          />
        ) : icon ? (
          <span className="shrink-0" aria-hidden="true">
            {icon}
          </span>
        ) : null}
        {children && <span>{children}</span>}
      </button>
    );
  },
);

Button.displayName = 'Button';