import {
  useEffect,
  useRef,
  useCallback,
  type ReactNode,
  type MouseEvent,
} from 'react';
import { X } from 'lucide-react';
import { cn } from '../../lib/utils';

const sizeStyles = {
  sm: 'max-w-sm',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
  full: 'max-w-[95vw] max-h-[95vh]',
} as const;

export interface ModalProps {
  /** Whether the modal is open */
  open: boolean;
  /** Called when the modal should close */
  onClose: () => void;
  /** Dialog size */
  size?: keyof typeof sizeStyles;
  /** Dialog title */
  title?: string;
  /** Optional description below the title */
  description?: string;
  /** Content of the modal body */
  children: ReactNode;
  /** Footer content (buttons etc) */
  footer?: ReactNode;
  /** Additional className for the panel */
  className?: string;
  /** Whether clicking the backdrop calls onClose */
  closeOnBackdrop?: boolean;
  /** Whether pressing Escape calls onClose */
  closeOnEscape?: boolean;
}

export function Modal({
  open,
  onClose,
  size = 'md',
  title,
  description,
  children,
  footer,
  className,
  closeOnBackdrop = true,
  closeOnEscape = true,
}: ModalProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  // Focus trap and body scroll lock
  useEffect(() => {
    if (!open) return;

    previousActiveElement.current = document.activeElement as HTMLElement;
    document.body.style.overflow = 'hidden';

    // Focus the panel on open
    const timer = setTimeout(() => {
      panelRef.current?.focus();
    }, 50);

    return () => {
      clearTimeout(timer);
      document.body.style.overflow = '';
      previousActiveElement.current?.focus();
    };
  }, [open]);

  // Escape key handler
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!open || !closeOnEscape) return;
      if (e.key === 'Escape') {
        onClose();
      }
      // Focus trap: keep focus inside the modal
      if (e.key === 'Tab' && panelRef.current) {
        const focusable = panelRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
        );
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    },
    [open, closeOnEscape, onClose],
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  const handleBackdropClick = useCallback(
    (e: MouseEvent) => {
      if (closeOnBackdrop && e.target === e.currentTarget) {
        onClose();
      }
    },
    [closeOnBackdrop, onClose],
  );

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? 'modal-title' : undefined}
      aria-describedby={description ? 'modal-desc' : undefined}
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm animate-fade-in"
        aria-hidden="true"
        onClick={handleBackdropClick}
      />

      {/* Panel */}
      <div
        ref={panelRef}
        tabIndex={-1}
        className={cn(
          'relative z-10 w-full rounded-t-xl sm:rounded-xl bg-white shadow-xl animate-slide-up',
          'focus:outline-none',
          'dark:bg-dark-surface dark:border dark:border-dark-border',
          sizeStyles[size],
          className,
        )}
      >
        {/* Header */}
        {(title || description) && (
          <div className="flex items-start justify-between px-6 pt-6 pb-3">
            <div className="flex-1 min-w-0 pr-4">
              {title && (
                <h2
                  id="modal-title"
                  className="text-lg font-semibold text-text-primary dark:text-dark-text-primary"
                >
                  {title}
                </h2>
              )}
              {description && (
                <p
                  id="modal-desc"
                  className="mt-1 text-sm text-text-secondary dark:text-dark-text-secondary"
                >
                  {description}
                </p>
              )}
            </div>
            <button
              type="button"
              onClick={onClose}
              className="shrink-0 rounded-lg p-1.5 text-text-tertiary hover:text-text-primary hover:bg-surface-secondary transition-colors dark:text-dark-text-tertiary dark:hover:text-dark-text-primary dark:hover:bg-dark-surface-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
              aria-label="Close dialog"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        )}

        {/* Body */}
        <div className={cn('px-6 py-3 overflow-y-auto max-h-[60vh]', !title && 'pt-6')}>
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="flex items-center justify-end gap-3 rounded-b-xl border-t border-border px-6 py-4 dark:border-dark-border">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}