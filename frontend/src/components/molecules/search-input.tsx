import { forwardRef, type InputHTMLAttributes } from 'react';
import { Search, Loader2, X } from 'lucide-react';
import { cn } from '../../lib/utils';

export interface SearchInputProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> {
  /** Show loading spinner */
  loading?: boolean;
  /** Called when the clear button is clicked */
  onClear?: () => void;
  /** Show clear button when value is present */
  clearable?: boolean;
  /** Size */
  size?: 'sm' | 'md';
}

export const SearchInput = forwardRef<HTMLInputElement, SearchInputProps>(
  (
    {
      className,
      loading = false,
      onClear,
      clearable = true,
      size = 'md',
      value,
      placeholder = 'Search...',
      ...props
    },
    ref,
  ) => {
    const sizeStyles = {
      sm: 'h-8 text-xs pl-9 pr-8',
      md: 'h-10 text-sm pl-10 pr-9',
    };

    const iconSizes = {
      sm: 'h-3.5 w-3.5',
      md: 'h-4 w-4',
    };

    const hasValue = value !== undefined && value !== '';

    return (
      <div className="relative w-full">
        <Search
          className={cn(
            'pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary dark:text-dark-text-tertiary',
            iconSizes[size],
          )}
          aria-hidden="true"
        />
        <input
          ref={ref}
          type="text"
          value={value}
          placeholder={placeholder}
          className={cn(
            'w-full rounded-lg border border-border bg-white transition-colors duration-150',
            'placeholder:text-text-tertiary dark:placeholder:text-dark-text-tertiary',
            'focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500',
            'dark:bg-transparent dark:border-dark-border dark:text-dark-text-primary dark:focus:border-brand-400',
            'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-gray-50 dark:disabled:bg-dark-surface-tertiary',
            sizeStyles[size],
            className,
          )}
          {...props}
        />
        <div className="absolute right-3 top-1/2 -translate-y-1/2">
          {loading ? (
            <Loader2
              className={cn(
                'animate-spin text-text-tertiary dark:text-dark-text-tertiary',
                iconSizes[size],
              )}
              aria-label="Searching"
            />
          ) : clearable && hasValue && onClear ? (
            <button
              type="button"
              onClick={onClear}
              className={cn(
                'rounded p-0.5 text-text-tertiary hover:text-text-primary transition-colors dark:text-dark-text-tertiary dark:hover:text-dark-text-primary',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
              )}
              aria-label="Clear search"
            >
              <X className={iconSizes[size]} />
            </button>
          ) : null}
        </div>
      </div>
    );
  },
);

SearchInput.displayName = 'SearchInput';