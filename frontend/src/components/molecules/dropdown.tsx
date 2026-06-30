import {
  useState,
  useRef,
  useEffect,
  useCallback,
  cloneElement,
  type ReactNode,
  type ReactElement,
  type HTMLAttributes,
  type KeyboardEvent,
} from 'react';
import { ChevronRight } from 'lucide-react';
import { cn } from '../../lib/utils';

export interface DropdownItem {
  /** Item label */
  label: string;
  /** Icon shown before the label */
  icon?: ReactNode;
  /** Click handler */
  onClick?: () => void;
  /** Show as disabled */
  disabled?: boolean;
  /** Danger variant (red text) */
  danger?: boolean;
  /** Render a divider instead of a clickable item */
  divider?: boolean;
  /** Submenu items */
  submenu?: DropdownItem[];
  /** Custom className */
  className?: string;
}

export interface DropdownProps extends HTMLAttributes<HTMLDivElement> {
  /** The trigger element */
  trigger: ReactElement<{ onClick?: () => void; ref?: React.Ref<unknown> }>;
  /** Menu items */
  items: DropdownItem[];
  /** Menu alignment relative to trigger */
  align?: 'start' | 'end';
  /** Called when menu opens/closes */
  onOpenChange?: (open: boolean) => void;
  /** Controlled open state */
  open?: boolean;
}

export function Dropdown({
  trigger,
  items,
  align = 'start',
  onOpenChange,
  open: controlledOpen,
  className,
  ...props
}: DropdownProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const isControlled = controlledOpen !== undefined;
  const isOpen = isControlled ? controlledOpen : internalOpen;

  const menuRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLElement>(null);
  const activeIndexRef = useRef(-1);

  const setIsOpen = useCallback(
    (val: boolean) => {
      if (!isControlled) setInternalOpen(val);
      onOpenChange?.(val);
    },
    [isControlled, onOpenChange],
  );

  // Click outside
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: MouseEvent) => {
      if (
        menuRef.current &&
        !menuRef.current.contains(e.target as Node) &&
        triggerRef.current &&
        !triggerRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [isOpen, setIsOpen]);

  // Focus first item on open
  useEffect(() => {
    if (!isOpen) return;
    const timer = setTimeout(() => {
      const items = menuRef.current?.querySelectorAll<HTMLElement>('[role="menuitem"]');
      if (items && items.length > 0) {
        items[0].focus();
        activeIndexRef.current = 0;
      }
    }, 50);
    return () => clearTimeout(timer);
  }, [isOpen]);

  const flatItems = items.filter((i) => !i.divider);

  const handleKeyDown = (e: KeyboardEvent) => {
    const menuItems = menuRef.current?.querySelectorAll<HTMLElement>(
      '[role="menuitem"]:not([data-submenu])',
    );
    if (!menuItems || menuItems.length === 0) return;

    let idx = activeIndexRef.current;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        idx = (idx + 1) % menuItems.length;
        break;
      case 'ArrowUp':
        e.preventDefault();
        idx = (idx - 1 + menuItems.length) % menuItems.length;
        break;
      case 'Enter':
      case ' ':
        e.preventDefault();
        menuItems[idx]?.click();
        return;
      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        triggerRef.current?.focus();
        return;
      default:
        return;
    }

    activeIndexRef.current = idx;
    menuItems[idx]?.focus();
  };

  // Nested submenu state
  const [activeSubmenu, setActiveSubmenu] = useState<number | null>(null);

  return (
    <div className={cn('relative inline-block', className)} {...props}>
      {/* Trigger */}
      {cloneElement(trigger, {
        ref: triggerRef,
        onClick: (e: MouseEvent) => {
          e.stopPropagation();
          trigger.props.onClick?.();
          setIsOpen(!isOpen);
        },
        'aria-expanded': isOpen,
        'aria-haspopup': 'menu',
      })}

      {/* Menu */}
      {isOpen && (
        <div
          ref={menuRef}
          role="menu"
          tabIndex={-1}
          onKeyDown={handleKeyDown}
          className={cn(
            'absolute z-50 mt-1 min-w-[200px] rounded-lg border border-border bg-white py-1 shadow-lg animate-fade-in dark:border-dark-border dark:bg-dark-surface',
            align === 'end' ? 'right-0' : 'left-0',
          )}
        >
          {items.map((item, i) => {
            if (item.divider) {
              return (
                <div
                  key={`divider-${i}`}
                  className="my-1 border-t border-border dark:border-dark-border"
                  role="separator"
                />
              );
            }

            const hasSubmenu = item.submenu && item.submenu.length > 0;
            const isSubmenuOpen = activeSubmenu === i;

            return (
              <div key={item.label} className="relative">
                <button
                  type="button"
                  role="menuitem"
                  disabled={item.disabled}
                  data-submenu={hasSubmenu ? 'true' : undefined}
                  className={cn(
                    'flex w-full items-center gap-2.5 px-3 py-2 text-sm text-left transition-colors',
                    'focus-visible:outline-none focus-visible:bg-surface-secondary dark:focus-visible:bg-dark-surface-secondary',
                    'disabled:opacity-40 disabled:cursor-not-allowed',
                    item.danger
                      ? 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20'
                      : 'text-text-primary dark:text-dark-text-primary hover:bg-surface-secondary dark:hover:bg-dark-surface-secondary',
                    item.className,
                  )}
                  onClick={() => {
                    if (hasSubmenu) {
                      setActiveSubmenu(isSubmenuOpen ? null : i);
                    } else {
                      item.onClick?.();
                      setIsOpen(false);
                    }
                  }}
                  onMouseEnter={() => {
                    if (hasSubmenu) setActiveSubmenu(i);
                  }}
                  onMouseLeave={() => {
                    if (hasSubmenu) setActiveSubmenu(null);
                  }}
                >
                  {item.icon && (
                    <span className="shrink-0 h-4 w-4 text-text-tertiary dark:text-dark-text-tertiary">
                      {item.icon}
                    </span>
                  )}
                  <span className="flex-1">{item.label}</span>
                  {hasSubmenu && (
                    <ChevronRight className="h-3.5 w-3.5 text-text-tertiary dark:text-dark-text-tertiary" />
                  )}
                </button>

                {/* Submenu */}
                {hasSubmenu && isSubmenuOpen && (
                  <div
                    role="menu"
                    className={cn(
                      'absolute top-0 left-full ml-1 min-w-[180px] rounded-lg border border-border bg-white py-1 shadow-lg dark:border-dark-border dark:bg-dark-surface',
                    )}
                  >
                    {item.submenu!.map((sub) => (
                      <button
                        key={sub.label}
                        type="button"
                        role="menuitem"
                        disabled={sub.disabled}
                        className={cn(
                          'flex w-full items-center gap-2.5 px-3 py-2 text-sm text-left transition-colors',
                          'focus-visible:outline-none focus-visible:bg-surface-secondary dark:focus-visible:bg-dark-surface-secondary',
                          'disabled:opacity-40 disabled:cursor-not-allowed',
                          sub.danger
                            ? 'text-red-600 dark:text-red-400'
                            : 'text-text-primary dark:text-dark-text-primary',
                          'hover:bg-surface-secondary dark:hover:bg-dark-surface-secondary',
                        )}
                        onClick={() => {
                          sub.onClick?.();
                          setIsOpen(false);
                        }}
                      >
                        {sub.icon && (
                          <span className="shrink-0 h-4 w-4 text-text-tertiary dark:text-dark-text-tertiary">
                            {sub.icon}
                          </span>
                        )}
                        {sub.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}