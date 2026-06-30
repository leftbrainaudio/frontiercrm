import { useState, type ReactNode } from 'react';
import { cn } from '../../lib/utils';
import { Badge } from '../atoms/badge';

export interface Tab {
  /** Tab label */
  label: string;
  /** Optional badge count */
  badge?: number;
  /** Optional icon */
  icon?: ReactNode;
  /** Disable this tab */
  disabled?: boolean;
  /** Tab id used for matching */
  id?: string;
}

export interface TabsProps {
  /** Array of tab definitions */
  tabs: Tab[];
  /** Active tab index (controlled) */
  activeIndex?: number;
  /** Default active tab index (uncontrolled) */
  defaultIndex?: number;
  /** Tab change handler */
  onChange?: (index: number) => void;
  /** Content renderer per tab */
  children?: (activeIndex: number) => ReactNode;
  /** Orientation */
  orientation?: 'horizontal' | 'vertical';
  /** Additional className */
  className?: string;
}

export function Tabs({
  tabs,
  activeIndex: controlledIndex,
  defaultIndex = 0,
  onChange,
  children,
  orientation = 'horizontal',
  className,
}: TabsProps) {
  const [internalIndex, setInternalIndex] = useState(defaultIndex);
  const isControlled = controlledIndex !== undefined;
  const activeIdx = isControlled ? controlledIndex : internalIndex;

  const handleClick = (idx: number) => {
    if (!isControlled) setInternalIndex(idx);
    onChange?.(idx);
  };

  const isVertical = orientation === 'vertical';

  return (
    <div className={cn(isVertical ? 'flex gap-4' : 'flex flex-col', className)}>
      {/* Tab list */}
      <div
        role="tablist"
        aria-orientation={orientation}
        className={cn(
          isVertical
            ? 'flex flex-col border-l border-border dark:border-dark-border'
            : 'flex border-b border-border dark:border-dark-border',
        )}
      >
        {tabs.map((tab, i) => {
          const isActive = activeIdx === i;
          return (
            <button
              key={tab.id ?? i}
              role="tab"
              aria-selected={isActive}
              aria-disabled={tab.disabled}
              tabIndex={isActive ? 0 : -1}
              disabled={tab.disabled}
              onClick={() => handleClick(i)}
              className={cn(
                'inline-flex items-center gap-2 whitespace-nowrap text-sm font-medium transition-colors',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900',
                'disabled:opacity-40 disabled:cursor-not-allowed',
                isVertical
                  ? 'px-4 py-2.5 border-l-2 -ml-px'
                  : 'px-4 py-2.5 border-b-2 -mb-px',
                isActive
                  ? cn(
                      'text-brand-600 dark:text-brand-400',
                      isVertical
                        ? 'border-l-brand-600 dark:border-l-brand-400 bg-brand-50/50 dark:bg-brand-900/20'
                        : 'border-b-brand-600 dark:border-b-brand-400',
                    )
                  : cn(
                      'text-text-secondary dark:text-dark-text-secondary border-transparent',
                      'hover:text-text-primary dark:hover:text-dark-text-primary hover:border-border dark:hover:border-dark-border',
                    ),
              )}
            >
              {tab.icon && (
                <span className="shrink-0 h-4 w-4" aria-hidden="true">
                  {tab.icon}
                </span>
              )}
              {tab.label}
              {tab.badge !== undefined && (
                <Badge variant="neutral" size="sm">
                  {tab.badge}
                </Badge>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab panels */}
      {children && (
        <div
          role="tabpanel"
          aria-labelledby={`tab-${activeIdx}`}
          className={cn('pt-4', isVertical && 'flex-1')}
        >
          {children(activeIdx)}
        </div>
      )}
    </div>
  );
}