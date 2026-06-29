import { Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';

const sizeStyles = {
  xs: 'h-3 w-3',
  sm: 'h-4 w-4',
  md: 'h-6 w-6',
  lg: 'h-8 w-8',
} as const;

const variantStyles = {
  brand: 'text-brand-600 dark:text-brand-400',
  white: 'text-white',
  muted: 'text-text-tertiary dark:text-dark-text-tertiary',
} as const;

export interface SpinnerProps {
  /** Size */
  size?: keyof typeof sizeStyles;
  /** Colour variant */
  variant?: keyof typeof variantStyles;
  /** Accessible label */
  label?: string;
  /** Full-page centered overlay */
  fullPage?: boolean;
  className?: string;
}

export function Spinner({
  size = 'md',
  variant = 'brand',
  label = 'Loading',
  fullPage = false,
  className,
}: SpinnerProps) {
  const spinner = (
    <Loader2
      className={cn('animate-spin', sizeStyles[size], variantStyles[variant], className)}
      role="status"
      aria-label={label}
    />
  );

  if (fullPage) {
    return (
      <div
        className="fixed inset-0 z-50 flex items-center justify-center bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm"
        role="alert"
        aria-busy="true"
      >
        <div className="flex flex-col items-center gap-3">
          {spinner}
          <span className="text-sm text-text-secondary dark:text-dark-text-secondary">
            {label}
          </span>
        </div>
      </div>
    );
  }

  return spinner;
}