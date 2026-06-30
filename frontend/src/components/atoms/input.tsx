import { forwardRef, type InputHTMLAttributes, type ReactNode } from 'react';
import { cn } from '../../lib/utils';

const sizeStyles = {
  sm: 'h-8 text-xs px-2.5',
  md: 'h-10 text-sm px-3',
} as const;

const variantStyles = {
  outline:
    'bg-white border border-border focus:border-brand-500 dark:bg-transparent dark:border-dark-border dark:text-dark-text-primary dark:focus:border-brand-400',
  filled:
    'bg-surface-secondary border border-transparent focus:bg-white focus:border-brand-500 dark:bg-dark-surface-secondary dark:text-dark-text-primary dark:focus:bg-dark-surface',
} as const;

const errorStyles =
  'border-red-500 focus:border-red-500 dark:border-red-400 dark:focus:border-red-400';

export interface InputProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> {
  /** Label displayed above the input */
  label?: string;
  /** Error message (shows in red) */
  error?: string;
  /** Helper text shown below */
  helperText?: string;
  /** Input size */
  size?: keyof typeof sizeStyles;
  /** Visual variant */
  variant?: keyof typeof variantStyles;
  /** Icon shown on the left inside the input */
  iconLeft?: ReactNode;
  /** Icon shown on the right inside the input */
  iconRight?: ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      label,
      error,
      helperText,
      size = 'md',
      variant = 'outline',
      iconLeft,
      iconRight,
      disabled,
      readOnly,
      id,
      ...props
    },
    ref,
  ) => {
    const inputId = id ?? (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="mb-1.5 block text-sm font-medium text-text-primary dark:text-dark-text-primary"
          >
            {label}
          </label>
        )}

        <div className="relative">
          {iconLeft && (
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-text-tertiary dark:text-dark-text-tertiary">
              {iconLeft}
            </div>
          )}

          <input
            ref={ref}
            id={inputId}
            disabled={disabled}
            readOnly={readOnly}
            aria-invalid={!!error || undefined}
            aria-describedby={
              error
                ? `${inputId}-error`
                : helperText
                  ? `${inputId}-helper`
                  : undefined
            }
            className={cn(
              'w-full rounded-lg transition-colors duration-150',
              'placeholder:text-text-tertiary dark:placeholder:text-dark-text-tertiary',
              'focus:outline-none focus:ring-2 focus:ring-brand-500/20',
              'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-gray-50 dark:disabled:bg-dark-surface-tertiary',
              'read-only:cursor-default read-only:bg-gray-50 dark:read-only:bg-dark-surface-tertiary',
              sizeStyles[size],
              variantStyles[variant],
              error && errorStyles,
              iconLeft && 'pl-10',
              iconRight && 'pr-10',
              className,
            )}
            {...props}
          />

          {iconRight && (
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3 text-text-tertiary dark:text-dark-text-tertiary">
              {iconRight}
            </div>
          )}
        </div>

        {error && (
          <p
            id={`${inputId}-error`}
            role="alert"
            className="mt-1.5 text-xs text-red-600 dark:text-red-400"
          >
            {error}
          </p>
        )}

        {!error && helperText && (
          <p
            id={`${inputId}-helper`}
            className="mt-1.5 text-xs text-text-tertiary dark:text-dark-text-tertiary"
          >
            {helperText}
          </p>
        )}
      </div>
    );
  },
);

Input.displayName = 'Input';