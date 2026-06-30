import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';

const variantStyles = {
  primary:
    'bg-brand-600 text-white hover:bg-brand-700 focus-visible:ring-brand-500 dark:bg-brand-500 dark:hover:bg-brand-600',
  secondary:
    'bg-surface-secondary text-text-primary hover:bg-surface-tertiary border border-border focus-visible:ring-brand-500 dark:bg-dark-surface-secondary dark:text-dark-text-primary dark:hover:bg-dark-surface-tertiary dark:border-dark-border',
  outline:
    'bg-transparent text-text-primary border-2 border-border hover:bg-surface-secondary hover:border-brand-500 focus-visible:ring-brand-500 dark:text-dark-text-primary dark:border-dark-border dark:hover:bg-dark-surface-secondary',
  ghost:
    'bg-transparent text-text-primary hover:bg-surface-secondary focus-visible:ring-brand-500 dark:text-dark-text-primary dark:hover:bg-dark-surface-secondary',
  danger:
    'bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500 dark:bg-red-500 dark:hover:bg-red-600',
} as const;

const sizeStyles = {
  xs: 'h-7 w-7',
  sm: 'h-8 w-8',
  md: 'h-10 w-10',
  lg: 'h-12 w-12',
} as const;

const iconSizes = {
  xs: 'h-3.5 w-3.5',
  sm: 'h-4 w-4',
  md: 'h-5 w-5',
  lg: 'h-6 w-6',
} as const;

export interface IconButtonProps
  extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'children'> {
  /** Icon element */
  icon: ReactNode;
  /** Accessible label */
  label: string;
  /** Visual variant */
  variant?: keyof typeof variantStyles;
  /** Size */
  size?: keyof typeof sizeStyles;
  /** Show loading spinner and disable interaction */
  loading?: boolean;
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  (
    {
      className,
      icon,
      label,
      variant = 'ghost',
      size = 'md',
      loading = false,
      disabled,
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
        aria-label={label}
        className={cn(
          'inline-flex items-center justify-center rounded-lg transition-all duration-150',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900',
          'disabled:pointer-events-none disabled:opacity-50',
          variantStyles[variant],
          sizeStyles[size],
          className,
        )}
        aria-busy={loading || undefined}
        {...props}
      >
        {loading ? (
          <Loader2 className={cn('animate-spin', iconSizes[size])} aria-hidden="true" />
        ) : (
          <span className={iconSizes[size]} aria-hidden="true">
            {icon}
          </span>
        )}
      </button>
    );
  },
);

IconButton.displayName = 'IconButton';