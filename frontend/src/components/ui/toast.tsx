import { toast as hotToast, type ToastOptions, type Toast } from 'react-hot-toast';
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react';
import { cn } from '../../lib/utils';

type ToastVariant = 'success' | 'error' | 'info' | 'warning';

const iconMap: Record<ToastVariant, typeof CheckCircle> = {
  success: CheckCircle,
  error: AlertCircle,
  info: Info,
  warning: AlertTriangle,
};

const variantStyles: Record<ToastVariant, string> = {
  success:
    'border-l-emerald-500 bg-emerald-50 dark:bg-emerald-900/20 dark:border-l-emerald-400',
  error: 'border-l-red-500 bg-red-50 dark:bg-red-900/20 dark:border-l-red-400',
  info: 'border-l-sky-500 bg-sky-50 dark:bg-sky-900/20 dark:border-l-sky-400',
  warning:
    'border-l-amber-500 bg-amber-50 dark:bg-amber-900/20 dark:border-l-amber-400',
};

const iconStyles: Record<ToastVariant, string> = {
  success: 'text-emerald-600 dark:text-emerald-400',
  error: 'text-red-600 dark:text-red-400',
  info: 'text-sky-600 dark:text-sky-400',
  warning: 'text-amber-600 dark:text-amber-400',
};

export interface ToastContent {
  /** Toast message */
  message: string;
  /** Optional description */
  description?: string;
  /** Action button config */
  action?: {
    label: string;
    onClick: () => void;
  };
}

export interface ToastFn {
  show: (message: string, options?: ToastOptions) => string;
  success: (content: string | ToastContent, options?: ToastOptions) => string;
  error: (content: string | ToastContent, options?: ToastOptions) => string;
  info: (content: string | ToastContent, options?: ToastOptions) => string;
  warning: (content: string | ToastContent, options?: ToastOptions) => string;
  dismiss: (toastId?: string) => void;
  dismissAll: () => void;
}

function renderToast(
  variant: ToastVariant,
  content: string | ToastContent,
  t: Toast,
): React.ReactNode {
  const isString = typeof content === 'string';
  const message = isString ? content : content.message;
  const description = !isString ? content.description : undefined;
  const action = !isString ? content.action : undefined;

  const Icon = iconMap[variant];

  return (
    <div
      className={cn(
        'pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-lg border border-border border-l-4 p-4 shadow-lg dark:border-dark-border',
        variantStyles[variant],
      )}
    >
      <Icon className={cn('h-5 w-5 shrink-0 mt-0.5', iconStyles[variant])} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-text-primary dark:text-dark-text-primary">
          {message}
        </p>
        {description && (
          <p className="mt-1 text-xs text-text-secondary dark:text-dark-text-secondary">
            {description}
          </p>
        )}
        {action && (
          <button
            type="button"
            onClick={action.onClick}
            className="mt-2 text-xs font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300 transition-colors"
          >
            {action.label}
          </button>
        )}
      </div>
      <button
        type="button"
        onClick={() => hotToast.dismiss(t.id)}
        className="shrink-0 rounded p-0.5 text-text-tertiary hover:text-text-primary transition-colors dark:text-dark-text-tertiary dark:hover:text-dark-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
        aria-label="Dismiss"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

const toastDefaults: ToastOptions = {
  duration: 4000,
  position: 'top-right',
};

export const toast: ToastFn = {
  show(message, options) {
    return hotToast(message, { ...toastDefaults, ...options });
  },

  success(content, options) {
    return hotToast.custom(
      (t) => renderToast('success', content, t),
      { ...toastDefaults, ...options, icon: undefined },
    );
  },

  error(content, options) {
    return hotToast.custom(
      (t) => renderToast('error', content, t),
      { ...toastDefaults, ...options, duration: 5000, icon: undefined },
    );
  },

  info(content, options) {
    return hotToast.custom(
      (t) => renderToast('info', content, t),
      { ...toastDefaults, ...options, icon: undefined },
    );
  },

  warning(content, options) {
    return hotToast.custom(
      (t) => renderToast('warning', content, t),
      { ...toastDefaults, ...options, duration: 5000, icon: undefined },
    );
  },

  dismiss(toastId) {
    hotToast.dismiss(toastId);
  },

  dismissAll() {
    hotToast.dismiss();
  },
};

export { Toaster } from 'react-hot-toast';