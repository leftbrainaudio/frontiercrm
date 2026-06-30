import { cn } from '../../lib/utils';

const variantStyles = {
  text: 'h-4 rounded',
  circular: 'rounded-full',
  rectangular: 'rounded-lg',
} as const;

export interface SkeletonProps {
  /** Shape variant */
  variant?: keyof typeof variantStyles;
  /** Width (Tailwind or arbitrary value) */
  width?: string | number;
  /** Height (Tailwind or arbitrary value) */
  height?: string | number;
  /** Number of skeleton lines to render (for text variant) */
  count?: number;
  /** Additional class names */
  className?: string;
  /** Disable the pulse animation */
  noAnimation?: boolean;
}

export function Skeleton({
  variant = 'text',
  width,
  height,
  count = 1,
  className,
  noAnimation = false,
}: SkeletonProps) {
  const resolveSize = (val: string | number | undefined): string | undefined => {
    if (val === undefined) return undefined;
    if (typeof val === 'number') return `${val}px`;
    return val;
  };

  const style: React.CSSProperties = {
    width: resolveSize(width),
    height: resolveSize(height),
  };

  const baseClass = cn(
    'bg-surface-tertiary dark:bg-dark-surface-tertiary',
    !noAnimation && 'animate-pulse',
    variantStyles[variant],
    className,
  );

  if (variant === 'text' && count > 1) {
    return (
      <div className="flex flex-col gap-2" role="status" aria-label="Loading">
        {Array.from({ length: count }).map((_, i) => (
          <div
            key={i}
            className={baseClass}
            style={{
              ...style,
              width: style.width ?? `${Math.max(60, 100 - i * 10)}%`,
            }}
          />
        ))}
        <span className="sr-only">Loading...</span>
      </div>
    );
  }

  return (
    <div
      className={baseClass}
      style={style}
      role="status"
      aria-label="Loading"
    >
      <span className="sr-only">Loading...</span>
    </div>
  );
}