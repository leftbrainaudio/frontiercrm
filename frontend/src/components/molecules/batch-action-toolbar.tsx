import { useMemo, type ReactNode } from 'react';
import { Button } from '../atoms/button';
import { Dropdown } from './dropdown';
import { BulkProgressBar } from './bulk-progress-bar';
import { useRole } from '../../hooks/useRole';
import { cn } from '../../lib/utils';
import {
  Trash2,
  UserCircle,
  GitBranch,
  ArrowUpDown,
  Tags,
  Download,
  X,
} from 'lucide-react';
import type { BulkJobStatus, BulkJob } from '../../types';

export interface BatchAction {
  id: string;
  label: string;
  icon?: ReactNode;
  /** The permission key required to see/use this action */
  permission?: string;
  /** This action opens a sub-dialog for additional input */
  requiresInput?: boolean;
  /** If true, this action is async and will be polled */
  async?: boolean;
  /** Group this action belongs to (for dropdown nesting) */
  group?: string;
}

export const DEFAULT_BULK_ACTIONS: Record<string, BatchAction[]> = {
  contact: [
    { id: 'delete', label: 'Delete', icon: <Trash2 className="h-4 w-4" />, permission: 'contacts.delete', requiresInput: true, async: true },
    { id: 'assign', label: 'Change Owner', icon: <UserCircle className="h-4 w-4" />, permission: 'contacts.edit', requiresInput: true, async: true },
    { id: 'add_tag', label: 'Add Tags', icon: <Tags className="h-4 w-4" />, permission: 'contacts.edit', requiresInput: true, async: true, group: 'tags' },
    { id: 'remove_tag', label: 'Remove Tags', icon: <Tags className="h-4 w-4" />, permission: 'contacts.edit', requiresInput: true, async: true, group: 'tags' },
    { id: 'export_csv', label: 'Export CSV', icon: <Download className="h-4 w-4" />, permission: 'contacts.view', async: false },
  ],
  deal: [
    { id: 'delete', label: 'Delete', icon: <Trash2 className="h-4 w-4" />, permission: 'deals.delete', requiresInput: true, async: true },
    { id: 'assign', label: 'Change Owner', icon: <UserCircle className="h-4 w-4" />, permission: 'deals.edit', requiresInput: true, async: true },
    { id: 'change_stage', label: 'Move Stage', icon: <GitBranch className="h-4 w-4" />, permission: 'deals.edit', requiresInput: true, async: true },
    { id: 'change_status', label: 'Change Status', icon: <ArrowUpDown className="h-4 w-4" />, permission: 'deals.edit', requiresInput: true, async: true },
    { id: 'add_tag', label: 'Add Tags', icon: <Tags className="h-4 w-4" />, permission: 'deals.edit', requiresInput: true, async: true, group: 'tags' },
    { id: 'remove_tag', label: 'Remove Tags', icon: <Tags className="h-4 w-4" />, permission: 'deals.edit', requiresInput: true, async: true, group: 'tags' },
    { id: 'export_csv', label: 'Export CSV', icon: <Download className="h-4 w-4" />, permission: 'deals.view', async: false },
  ],
  account: [
    { id: 'delete', label: 'Delete', icon: <Trash2 className="h-4 w-4" />, permission: 'contacts.delete', requiresInput: true, async: true },
    { id: 'add_tag', label: 'Add Tags', icon: <Tags className="h-4 w-4" />, permission: 'contacts.edit', requiresInput: true, async: true, group: 'tags' },
    { id: 'remove_tag', label: 'Remove Tags', icon: <Tags className="h-4 w-4" />, permission: 'contacts.edit', requiresInput: true, async: true, group: 'tags' },
    { id: 'export_csv', label: 'Export CSV', icon: <Download className="h-4 w-4" />, permission: 'contacts.view', async: false },
  ],
};

export interface BatchActionToolbarProps {
  selectedCount: number;
  totalCount?: number;
  /** Whether selection covers all matching records (not just this page) */
  isSelectAllMatching?: boolean;
  currentFilterParams?: Record<string, string>;
  entityType: 'contact' | 'deal' | 'account';
  actions?: BatchAction[];
  onAction: (actionId: string, extraData?: Record<string, unknown>) => void;
  onClear: () => void;
  /** Current async job state (shows progress bar instead of actions) */
  currentJob?: {
    status: BulkJobStatus;
    total: number;
    processed: number;
    errors: number;
  } | null;
  /** Job result message (shown after completion) */
  jobResult?: {
    message: string;
    type: 'success' | 'error' | 'partial';
  } | null;
  onDismissResult?: () => void;
  onCancelJob?: () => void;
  loading?: boolean;
}

export function BatchActionToolbar({
  selectedCount,
  totalCount,
  isSelectAllMatching = false,
  currentFilterParams,
  entityType,
  actions,
  onAction,
  onClear,
  currentJob,
  jobResult,
  onDismissResult,
  onCancelJob,
  loading = false,
}: BatchActionToolbarProps) {
  const { hasPermission } = useRole();

  const visibleActions = useMemo(() => {
    const source = actions ?? DEFAULT_BULK_ACTIONS[entityType] ?? [];
    return source.filter((a) => {
      if (!a.permission) return true;
      return hasPermission(a.permission);
    });
  }, [actions, entityType, hasPermission]);

  // Split actions into direct buttons and tag-grouped dropdown items
  const { directActions, tagActions } = useMemo(() => {
    const direct: BatchAction[] = [];
    const tag: BatchAction[] = [];
    for (const a of visibleActions) {
      if (a.group === 'tags') {
        tag.push(a);
      } else {
        direct.push(a);
      }
    }
    return { directActions: direct, tagActions: tag };
  }, [visibleActions]);

  // ── Progress / result state ──

  if (jobResult) {
    return (
      <div
        className={cn(
          'flex items-center justify-between gap-4 rounded-lg border px-4 py-3 shadow-sm',
          jobResult.type === 'success' && 'border-emerald-200 bg-emerald-50 dark:border-emerald-800 dark:bg-emerald-900/20',
          jobResult.type === 'error' && 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20',
          jobResult.type === 'partial' && 'border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-900/20',
        )}
        role="status"
        aria-live="polite"
      >
        <p className="text-sm font-medium text-text-primary dark:text-dark-text-primary">
          {jobResult.message}
        </p>
        {onDismissResult && (
          <Button variant="ghost" size="sm" onClick={onDismissResult}>
            Dismiss
          </Button>
        )}
      </div>
    );
  }

  if (currentJob) {
    return (
      <div className="flex items-center justify-between gap-4 rounded-lg border border-border bg-surface-secondary px-4 py-3 shadow-sm dark:border-dark-border dark:bg-dark-surface-secondary">
        <div className="flex-1 min-w-0">
          <BulkProgressBar
            processed={currentJob.processed}
            total={currentJob.total}
            status={currentJob.status}
          />
        </div>
        {(currentJob.status === 'pending' || currentJob.status === 'running') && onCancelJob && (
          <Button variant="ghost" size="sm" onClick={onCancelJob}>
            Cancel
          </Button>
        )}
      </div>
    );
  }

  // ── Default state — show action buttons ──
  return (
    <div className="flex items-center justify-between gap-4 rounded-lg border border-border bg-surface-secondary px-4 py-3 shadow-sm dark:border-dark-border dark:bg-dark-surface-secondary">
      <div className="flex items-center gap-2 text-sm text-text-secondary dark:text-dark-text-secondary">
        <span className="font-medium text-text-primary dark:text-dark-text-primary">
          {selectedCount.toLocaleString()}
        </span>{' '}
        selected
        {totalCount !== undefined && isSelectAllMatching && (
          <span className="text-text-tertiary dark:text-dark-text-tertiary">
            (of {totalCount.toLocaleString()} matching)
          </span>
        )}
        <button
          type="button"
          onClick={onClear}
          className="ml-1 text-xs text-brand-600 hover:text-brand-700 underline dark:text-brand-400 dark:hover:text-brand-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
        >
          Clear selection
        </button>
      </div>

      <div className="flex items-center gap-2">
        {directActions.map((action) => (
          <Button
            key={action.id}
            variant="secondary"
            size="sm"
            icon={action.icon}
            loading={loading && !action.requiresInput}
            onClick={() => onAction(action.id)}
          >
            {action.label}
          </Button>
        ))}

        {tagActions.length > 0 && (
          <Dropdown
            trigger={
              <Button variant="secondary" size="sm" icon={<Tags className="h-4 w-4" />}>
                Tags
              </Button>
            }
            items={tagActions.map((a) => ({
              label: a.label,
              icon: a.icon,
              onClick: () => onAction(a.id),
              disabled: loading,
            }))}
            align="end"
          />
        )}
      </div>
    </div>
  );
}
