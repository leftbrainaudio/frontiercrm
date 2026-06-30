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

const sizeStyles = {
  sm: 'px-1.5 py-0.5 text-[11px]',
  md: 'px-2 py-0.5 text-xs',
  lg: 'px-2.5 py-1 text-sm',
} as const;

export interface TagProps extends HTMLAttributes<HTMLSpanElement> {
  /** Colour variant */
  variant?: keyof typeof variantStyles;
  /** Size */
  size?: keyof typeof sizeStyles;
  /** Show removable X button */
  onRemove?: () => void;
}

export function Tag({
  className,
  variant = 'default',
  size = 'md',
  onRemove,
  children,
  ...props
}: TagProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-md font-medium leading-none',
        variantStyles[variant],
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
          className="ml-0.5 rounded p-0.5 hover:bg-black/10 dark:hover:bg-white/10 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
          aria-label="Remove tag"
        >
          <X className={cn(size === 'sm' ? 'h-2.5 w-2.5' : 'h-3 w-3')} />
        </button>
      )}
    </span>
  );
}