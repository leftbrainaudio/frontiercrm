import { forwardRef, type SelectHTMLAttributes } from 'react';
import { cn } from '../../lib/utils';
import { ChevronDown } from 'lucide-react';

const sizeStyles = {
  sm: 'h-8 text-xs px-2.5 pr-7',
  md: 'h-10 text-sm px-3 pr-9',
} as const;

const variantStyles = {
  outline:
    'bg-white border border-border focus:border-brand-500 dark:bg-transparent dark:border-dark-border dark:text-dark-text-primary dark:focus:border-brand-400',
  filled:
    'bg-surface-secondary border border-transparent focus:bg-white focus:border-brand-500 dark:bg-dark-surface-secondary dark:text-dark-text-primary dark:focus:bg-dark-surface',
} as const;

export interface SelectProps
  extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'size'> {
  /** Label displayed above the select */
  label?: string;
  /** Error message (shows in red) */
  error?: string;
  /** Helper text shown below */
  helperText?: string;
  /** Select size */
  size?: keyof typeof sizeStyles;
  /** Visual variant */
  variant?: keyof typeof variantStyles;
  /** Placeholder option (disabled) */
  placeholder?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  (
    {
      className,
      label,
      error,
      helperText,
      size = 'md',
      variant = 'outline',
      placeholder,
      children,
      id,
      ...props
    },
    ref,
  ) => {
    const selectId = id ?? (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={selectId}
            className="mb-1.5 block text-sm font-medium text-text-primary dark:text-dark-text-primary"
          >
            {label}
          </label>
        )}

        <div className="relative">
          <select
            ref={ref}
            id={selectId}
            aria-invalid={!!error || undefined}
            aria-describedby={
              error
                ? `${selectId}-error`
                : helperText
                  ? `${selectId}-helper`
                  : undefined
            }
            className={cn(
              'w-full rounded-lg transition-colors duration-150 appearance-none cursor-pointer',
              'focus:outline-none focus:ring-2 focus:ring-brand-500/20',
              'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-gray-50 dark:disabled:bg-dark-surface-tertiary',
              sizeStyles[size],
              variantStyles[variant],
              error && 'border-red-500 focus:border-red-500 dark:border-red-400 dark:focus:border-red-400',
              className,
            )}
            {...props}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {children}
          </select>
          <ChevronDown
            className={cn(
              'pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-text-tertiary dark:text-dark-text-tertiary',
              size === 'sm' ? 'h-3.5 w-3.5' : 'h-4 w-4',
            )}
          />
        </div>

        {error && (
          <p
            id={`${selectId}-error`}
            role="alert"
            className="mt-1.5 text-xs text-red-600 dark:text-red-400"
          >
            {error}
          </p>
        )}

        {!error && helperText && (
          <p
            id={`${selectId}-helper`}
            className="mt-1.5 text-xs text-text-tertiary dark:text-dark-text-tertiary"
          >
            {helperText}
          </p>
        )}
      </div>
    );
  },
);

Select.displayName = 'Select';