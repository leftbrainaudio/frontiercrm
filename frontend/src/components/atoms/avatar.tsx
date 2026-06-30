import { type HTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

const sizeStyles = {
  xs: 'h-6 w-6 text-[10px]',
  sm: 'h-8 w-8 text-xs',
  md: 'h-10 w-10 text-sm',
  lg: 'h-12 w-12 text-base',
  xl: 'h-16 w-16 text-xl',
} as const;

const indicatorSizes = {
  xs: 'h-1.5 w-1.5 right-0 top-0',
  sm: 'h-2 w-2 right-0 top-0',
  md: 'h-2.5 w-2.5 right-0 top-0',
  lg: 'h-3 w-3 right-0.5 top-0.5',
  xl: 'h-3.5 w-3.5 right-0.5 top-0.5',
} as const;

export interface AvatarProps extends HTMLAttributes<HTMLDivElement> {
  /** Image URL */
  src?: string;
  /** Alt text */
  alt?: string;
  /** Size */
  size?: keyof typeof sizeStyles;
  /** Fallback initials (shown when no image or image fails to load) */
  fallback?: string;
  /** Show online indicator dot */
  online?: boolean;
  /** Shape */
  shape?: 'circle' | 'square';
}

function getInitials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase();
}

export function Avatar({
  className,
  src,
  alt = '',
  size = 'md',
  fallback,
  online = false,
  shape = 'circle',
  ...props
}: AvatarProps) {
  const shapeStyles = shape === 'circle' ? 'rounded-full' : 'rounded-lg';

  return (
    <div className={cn('relative inline-flex shrink-0', className)} {...props}>
      {src ? (
        <img
          src={src}
          alt={alt}
          className={cn(sizeStyles[size], shapeStyles, 'object-cover bg-surface-secondary dark:bg-dark-surface-secondary')}
          onError={(e) => {
            // Hide the image on error; fallback will be shown via CSS sibling
            (e.currentTarget as HTMLImageElement).style.display = 'none';
          }}
        />
      ) : null}

      {/* Fallback – visible when no src or when img is hidden due to error */}
      {(!src || fallback) && (
        <span
          className={cn(
            'inline-flex items-center justify-center font-medium text-text-secondary dark:text-dark-text-secondary bg-surface-secondary dark:bg-dark-surface-secondary',
            sizeStyles[size],
            shapeStyles,
          )}
          aria-hidden={!!src}
          role={!src ? 'img' : undefined}
          aria-label={!src ? alt : undefined}
        >
          {fallback && getInitials(fallback)}
        </span>
      )}

      {online && (
        <span
          className={cn(
            'absolute block rounded-full border-2 border-white dark:border-dark-surface bg-emerald-500',
            indicatorSizes[size],
          )}
          aria-label="Online"
          role="status"
        />
      )}
    </div>
  );
}