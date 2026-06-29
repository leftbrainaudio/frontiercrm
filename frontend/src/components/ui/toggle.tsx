import { forwardRef, type InputHTMLAttributes, type ReactNode } from 'react';
import { cn } from '../../lib/utils';

const sizeStyles = {
  sm: 'h-4 w-4',
  md: 'h-5 w-5',
} as const;

const thumbSizes = {
  sm: 'h-3 w-3',
  md: 'h-4 w-4',
} as const;

export interface ToggleProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size' | 'type'> {
  /** Visual size */
  size?: keyof typeof sizeStyles;
  /** Label text */
  label?: string;
  /** Label position */
  labelPosition?: 'left' | 'right';
}

export const Toggle = forwardRef<HTMLInputElement, ToggleProps>(
  (
    {
      className,
      size = 'md',
      label,
      labelPosition = 'right',
      disabled,
      id,
      ...props
    },
    ref,
  ) => {
    const inputId = id ?? label ? label.toLowerCase().replace(/\s+/g, '-') : undefined;

    const input = (
      <input
        ref={ref}
        id={inputId}
        type="checkbox"
        role="switch"
        disabled={disabled}
        className={cn(
          'peer appearance-none rounded-full transition-colors duration-200',
          'bg-gray-200 dark:bg-dark-surface-tertiary',
          'checked:bg-brand-600 dark:checked:bg-brand-500',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900',
          'disabled:cursor-not-allowed disabled:opacity-50',
          'cursor-pointer',
          sizeStyles[size],
          className,
        )}
        {...props}
      />
    );

    const thumb = (
      <span
        className={cn(
          'pointer-events-none absolute top-1/2 -translate-y-1/2 rounded-full bg-white shadow-sm transition-all duration-200 peer-checked:left-[calc(100%-4px)] peer-checked:-translate-x-full',
          size === 'sm'
            ? 'left-0.5'
            : 'left-0.5',
          thumbSizes[size],
          'peer-checked:bg-white',
        )}
        aria-hidden="true"
      />
    );

    if (!label) {
      return (
        <span className={cn('relative inline-flex shrink-0', sizeStyles[size])}>
          {input}
          {thumb}
        </span>
      );
    }

    return (
      <label
        htmlFor={inputId}
        className={cn(
          'inline-flex items-center gap-3 cursor-pointer',
          disabled && 'cursor-not-allowed opacity-50',
        )}
      >
        {labelPosition === 'left' && (
          <span className="text-sm font-medium text-text-primary dark:text-dark-text-primary select-none">
            {label}
          </span>
        )}
        <span className={cn('relative inline-flex shrink-0', sizeStyles[size])}>
          {input}
          {thumb}
        </span>
        {labelPosition === 'right' && (
          <span className="text-sm font-medium text-text-primary dark:text-dark-text-primary select-none">
            {label}
          </span>
        )}
      </label>
    );
  },
);

Toggle.displayName = 'Toggle';