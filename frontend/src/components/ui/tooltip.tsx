import {
  useState,
  useRef,
  useCallback,
  type ReactNode,
  type ReactElement,
} from 'react';
import { cn } from '../../lib/utils';

const positionStyles = {
  top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
  bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
  left: 'right-full top-1/2 -translate-y-1/2 mr-2',
  right: 'left-full top-1/2 -translate-y-1/2 ml-2',
} as const;

const arrowStyles = {
  top: 'top-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-b-transparent border-t-gray-900 dark:border-t-slate-700',
  bottom:
    'bottom-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-t-transparent border-b-gray-900 dark:border-b-slate-700',
  left: 'left-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-r-transparent border-l-gray-900 dark:border-l-slate-700',
  right:
    'right-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-l-transparent border-r-gray-900 dark:border-r-slate-700',
} as const;

export interface TooltipProps {
  /** Tooltip content */
  content: ReactNode;
  /** The trigger element */
  children: ReactElement;
  /** Tooltip position */
  position?: keyof typeof positionStyles;
  /** Delay in ms before showing */
  showDelay?: number;
  /** Delay in ms before hiding */
  hideDelay?: number;
  /** Show arrow indicator */
  arrow?: boolean;
  /** Additional className */
  className?: string;
}

export function Tooltip({
  content,
  children,
  position = 'top',
  showDelay = 300,
  hideDelay = 150,
  arrow = true,
  className,
}: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const showTimer = useRef<ReturnType<typeof setTimeout>>();
  const hideTimer = useRef<ReturnType<typeof setTimeout>>();

  const handleMouseEnter = useCallback(() => {
    clearTimeout(hideTimer.current);
    showTimer.current = setTimeout(() => setVisible(true), showDelay);
  }, [showDelay]);

  const handleMouseLeave = useCallback(() => {
    clearTimeout(showTimer.current);
    hideTimer.current = setTimeout(() => setVisible(false), hideDelay);
  }, [hideDelay]);

  const handleFocus = useCallback(() => {
    clearTimeout(hideTimer.current);
    setVisible(true);
  }, []);

  const handleBlur = useCallback(() => {
    setVisible(false);
  }, []);

  return (
    <div
      className="relative inline-flex"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onFocus={handleFocus}
      onBlur={handleBlur}
    >
      {children}

      {visible && (
        <div
          role="tooltip"
          className={cn(
            'absolute z-[60] pointer-events-none',
            positionStyles[position],
            className,
          )}
        >
          <div className="rounded-md bg-gray-900 px-2.5 py-1.5 text-xs text-white shadow-lg whitespace-nowrap dark:bg-slate-700 dark:text-slate-100">
            {content}
          </div>
          {arrow && (
            <div
              className={cn(
                'absolute w-0 h-0 border-[5px]',
                arrowStyles[position],
              )}
            />
          )}
        </div>
      )}
    </div>
  );
}