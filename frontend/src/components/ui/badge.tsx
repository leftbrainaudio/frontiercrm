import { type HTMLAttributes } from 'react';
import { X } from 'lucide-react';
import { cn } from '../../lib/utils';

const variantStyles = {
  default:
    'bg-brand-100 text-brand-800 dark:bg-brand-900/40 dark:text-brand-300',
  success:
    'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300',
  warning:
    'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300',
  danger: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300',
  info: 'bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-300',
  neutral:
    'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
} as const;

const outlineVariantStyles = {
  default: 'border-brand-500 text-brand-700 dark:text-brand-300',
  success: 'border-emerald-500 text-emerald-700 dark:text-emerald-300',
  warning: 'border-amber-500 text-amber-700 dark:text-amber-300',
  danger: 'border-red-500 text-red-700 dark:text-red-300',
  info: 'border-sky-500 text-sky-700 dark:text-sky-300',
  neutral: 'border-gray-500 text-gray-700 dark:text-gray-300',
} as const;

const dotStyles = {
  default: 'bg-brand-500',
  success: 'bg-emerald-500',
  warning: 'bg-amber-500',
  danger: 'bg-red-500',
  info: 'bg-sky-500',
  neutral: 'bg-gray-500',
} as const;

const sizeStyles = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-sm',
} as const;

type BadgeVariant = keyof typeof variantStyles;

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  /** Colour variant */
  variant?: BadgeVariant;
  /** Size */
  size?: keyof typeof sizeStyles;
  /** Show as dot indicator (no text, small circle) */
  dot?: boolean;
  /** Show outline style instead of solid */
  outline?: boolean;
  /** Show removable X button, calls this on click */
  onRemove?: () => void;
}

export function Badge({
  className,
  variant = 'default',
  size = 'md',
  dot = false,
  outline = false,
  onRemove,
  children,
  ...props
}: BadgeProps) {
  if (dot) {
    return (
      <span
        className={cn('inline-block rounded-full', dotStyles[variant], className)}
        aria-label="Indicator"
        role="status"
        style={{ width: size === 'sm' ? 6 : 8, height: size === 'sm' ? 6 : 8 }}
        {...props}
      />
    );
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full font-medium leading-none',
        outline
          ? 'bg-transparent border'
          : variantStyles[variant],
        outline && outlineVariantStyles[variant],
        sizeStyles[size],
        className,
      )}
      {...props}
    >
      {children}
      {onRemove && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          className="ml-0.5 rounded-full p-0.5 hover:bg-black/10 dark:hover:bg-white/10 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
          aria-label="Remove"
        >
          <X className={cn(size === 'sm' ? 'h-2.5 w-2.5' : 'h-3 w-3')} />
        </button>
      )}
    </span>
  );
}