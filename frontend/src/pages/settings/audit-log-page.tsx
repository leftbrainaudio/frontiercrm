import { useState, useMemo } from 'react';
import { History, AlertCircle, Search, X } from 'lucide-react';
import { useAuditLog } from '../../api/audit';
import { Table } from '../../components/ui/table';
import { ErrorState } from '../../components/ui/error-state';
import { EmptyState } from '../../components/ui/empty-state';
import { Input } from '../../components/atoms/input';
import { Button } from '../../components/atoms/button';
import { Skeleton } from '../../components/atoms/skeleton';
import { cn } from '../../lib/utils';
import type { AuditLogEntry } from '../../types';

const PAGE_SIZE = 25;

const ENTITY_TYPE_OPTIONS = [
  { value: '', label: 'All Types' },
  { value: 'contact', label: 'Contact' },
  { value: 'deal', label: 'Deal' },
  { value: 'account', label: 'Account' },
  { value: 'note', label: 'Note' },
  { value: 'email', label: 'Email' },
  { value: 'task', label: 'Task' },
  { value: 'activity', label: 'Activity' },
  { value: 'user', label: 'User' },
  { value: 'team', label: 'Team' },
  { value: 'role', label: 'Role' },
  { value: 'webhook', label: 'Webhook' },
  { value: 'file', label: 'File' },
];

const ACTION_OPTIONS = [
  { value: '', label: 'All Actions' },
  { value: 'create', label: 'Created' },
  { value: 'update', label: 'Updated' },
  { value: 'delete', label: 'Deleted' },
  { value: 'login', label: 'Login' },
  { value: 'export', label: 'Export' },
  { value: 'import', label: 'Import' },
  { value: 'invite', label: 'Invited' },
  { value: 'send', label: 'Sent' },
  { value: 'archive', label: 'Archived' },
  { value: 'restore', label: 'Restored' },
];

type FilterKey = 'entity_type' | 'action' | 'actor_id' | 'date_from' | 'date_to';

function FilterChip({
  label,
  onRemove,
}: {
  label: string;
  onRemove: () => void;
}) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-medium text-brand-700 dark:bg-brand-900/30 dark:text-brand-300">
      {label}
      <button
        onClick={onRemove}
        className="ml-0.5 inline-flex h-3.5 w-3.5 items-center justify-center rounded-full hover:bg-brand-200 dark:hover:bg-brand-800"
        aria-label={`Remove filter: ${label}`}
      >
        <X className="h-2.5 w-2.5" />
      </button>
    </span>
  );
}

function timestampDisplay(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function ActionBadge({ action }: { action: string }) {
  const colors: Record<string, string> = {
    create: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
    update: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
    delete: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
    login: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
    export: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
    import: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300',
    invite: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300',
    send: 'bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-300',
    archive: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
    restore: 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
        colors[action] || 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
      )}
    >
      {action}
    </span>
  );
}

function Capitalize({ text }: { text: string }) {
  return <>{text.charAt(0).toUpperCase() + text.slice(1)}</>;
}

const columns = [
  {
    header: 'Timestamp',
    accessor: 'created_at' as keyof AuditLogEntry,
    sortable: true,
    width: '180px',
    cell: (row: AuditLogEntry) => (
      <span className="text-xs text-text-secondary dark:text-dark-text-secondary whitespace-nowrap">
        {timestampDisplay(row.created_at)}
      </span>
    ),
  },
  {
    header: 'User',
    accessor: 'actor_name' as keyof AuditLogEntry,
    width: '180px',
    cell: (row: AuditLogEntry) => (
      <span className="text-sm text-text-primary dark:text-dark-text-primary">
        {row.actor_name}
      </span>
    ),
  },
  {
    header: 'Action',
    accessor: 'action' as keyof AuditLogEntry,
    sortable: true,
    width: '100px',
    cell: (row: AuditLogEntry) => <ActionBadge action={row.action} />,
  },
  {
    header: 'Entity Type',
    accessor: 'entity_type' as keyof AuditLogEntry,
    sortable: true,
    width: '120px',
    cell: (row: AuditLogEntry) => (
      <span className="text-sm text-text-primary dark:text-dark-text-primary capitalize">
        <Capitalize text={row.entity_type} />
      </span>
    ),
  },
  {
    header: 'Entity Name',
    accessor: 'entity_name' as keyof AuditLogEntry,
    width: '1fr',
    cell: (row: AuditLogEntry) => (
      <span className="text-sm text-text-primary dark:text-dark-text-primary">
        {row.entity_name || '—'}
      </span>
    ),
  },
  {
    header: 'Details',
    accessor: 'details' as keyof AuditLogEntry,
    width: '200px',
    cell: (row: AuditLogEntry) => {
      const details = row.details;
      if (!details || Object.keys(details).length === 0) {
        return <span className="text-xs text-text-tertiary">—</span>;
      }
      return (
        <span className="text-xs text-text-tertiary dark:text-dark-text-tertiary truncate block max-w-[200px]" title={JSON.stringify(details)}>
          {JSON.stringify(details)}
        </span>
      );
    },
  },
];

export default function AuditLogPage() {
  const [entityType, setEntityType] = useState('');
  const [action, setAction] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [page, setPage] = useState(1);

  const filters = useMemo(
    () => ({
      entity_type: entityType || undefined,
      action: action || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      page,
      page_size: PAGE_SIZE,
    }),
    [entityType, action, dateFrom, dateTo, page],
  );

  const { data, isLoading, isError, error, refetch } = useAuditLog(filters);

  const entries: AuditLogEntry[] = data?.results ?? [];
  const totalCount = data?.count ?? 0;
  const totalPages = data ? Math.ceil(data.count / PAGE_SIZE) : 0;

  const activeFilterCount = [entityType, action, dateFrom, dateTo].filter(Boolean).length;

  const clearAllFilters = () => {
    setEntityType('');
    setAction('');
    setDateFrom('');
    setDateTo('');
    setPage(1);
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      {/* Page header */}
      <div className="mb-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-surface-secondary dark:bg-dark-surface-secondary">
            <History className="h-5 w-5 text-text-secondary dark:text-dark-text-secondary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-text-primary dark:text-dark-text-primary">
              Audit Log
            </h1>
            <p className="mt-1 text-sm text-text-secondary dark:text-dark-text-secondary">
              Track user activity and changes across your CRM ({totalCount} entries)
            </p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-4 rounded-xl border border-border bg-surface p-4 dark:border-dark-border dark:bg-dark-surface">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {/* Entity Type Filter */}
          <div>
            <label className="mb-1.5 block text-xs font-medium text-text-secondary dark:text-dark-text-secondary">
              Entity Type
            </label>
            <select
              value={entityType}
              onChange={(e) => {
                setEntityType(e.target.value);
                setPage(1);
              }}
              className="w-full rounded-lg border border-border bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary"
            >
              {ENTITY_TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Action Filter */}
          <div>
            <label className="mb-1.5 block text-xs font-medium text-text-secondary dark:text-dark-text-secondary">
              Action
            </label>
            <select
              value={action}
              onChange={(e) => {
                setAction(e.target.value);
                setPage(1);
              }}
              className="w-full rounded-lg border border-border bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary"
            >
              {ACTION_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Date From */}
          <div>
            <label className="mb-1.5 block text-xs font-medium text-text-secondary dark:text-dark-text-secondary">
              From Date
            </label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => {
                setDateFrom(e.target.value);
                setPage(1);
              }}
              className="w-full rounded-lg border border-border bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary"
            />
          </div>

          {/* Date To */}
          <div>
            <label className="mb-1.5 block text-xs font-medium text-text-secondary dark:text-dark-text-secondary">
              To Date
            </label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => {
                setDateTo(e.target.value);
                setPage(1);
              }}
              className="w-full rounded-lg border border-border bg-white px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary"
            />
          </div>
        </div>

        {/* Active filter chips */}
        {activeFilterCount > 0 && (
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <span className="text-xs text-text-tertiary dark:text-dark-text-tertiary">
              Active filters:
            </span>
            {entityType && (
              <FilterChip
                label={`Type: ${ENTITY_TYPE_OPTIONS.find((o) => o.value === entityType)?.label || entityType}`}
                onRemove={() => { setEntityType(''); setPage(1); }}
              />
            )}
            {action && (
              <FilterChip
                label={`Action: ${ACTION_OPTIONS.find((o) => o.value === action)?.label || action}`}
                onRemove={() => { setAction(''); setPage(1); }}
              />
            )}
            {dateFrom && (
              <FilterChip
                label={`From: ${dateFrom}`}
                onRemove={() => { setDateFrom(''); setPage(1); }}
              />
            )}
            {dateTo && (
              <FilterChip
                label={`To: ${dateTo}`}
                onRemove={() => { setDateTo(''); setPage(1); }}
              />
            )}
            <button
              onClick={clearAllFilters}
              className="text-xs text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300 underline"
            >
              Clear all
            </button>
          </div>
        )}
      </div>

      {/* Content area */}
      {isError ? (
        <ErrorState
          title="Failed to load audit log"
          description={(error as any)?.message || 'An error occurred while fetching the audit log.'}
          onRetry={() => refetch()}
        />
      ) : isLoading ? (
        <div className="space-y-3">
          <Skeleton width="100%" height={48} />
          <Skeleton width="100%" height={48} />
          <Skeleton width="100%" height={48} />
          <Skeleton width="100%" height={48} />
          <Skeleton width="100%" height={48} />
        </div>
      ) : entries.length === 0 ? (
        <EmptyState
          icon={<History className="h-8 w-8" />}
          title="No audit entries found"
          description={
            activeFilterCount > 0
              ? 'No entries match your current filters. Try adjusting them.'
              : 'No activity has been logged yet. Actions will appear here as users interact with the CRM.'
          }
        />
      ) : (
        <>
          <Table
            columns={columns}
            data={entries}
            loading={false}
            bordered
            striped
          />

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-4 flex items-center justify-between">
              <p className="text-sm text-text-secondary dark:text-dark-text-secondary">
                Page {page} of {totalPages} ({totalCount} total entries)
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
