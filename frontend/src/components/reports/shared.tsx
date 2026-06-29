import type { ReactNode } from 'react';
import type { DashboardReport, StaleDeal } from '../../types';

// ── Shared formatters ───────────────────────────────────────────────

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function formatChange(value: number | null): string {
  if (value === null) return '—';
  const prefix = value >= 0 ? '+' : '';
  return `${prefix}${value.toFixed(1)}%`;
}

export function formatChangeAbsolute(value: number | null): string {
  if (value === null) return '—';
  const prefix = value >= 0 ? '+' : '';
  return `${prefix}${value}`;
}

export function isPositiveChange(value: number | null): boolean {
  if (value === null) return true;
  return value >= 0;
}

// ── Chart colours ──────────────────────────────────────────────────

export const CHART_COLORS = [
  '#6366f1', // brand-500
  '#22c55e', // emerald-500
  '#f59e0b', // amber-500
  '#ef4444', // red-500
  '#3b82f6', // blue-500
  '#8b5cf6', // violet-500
  '#ec4899', // pink-500
  '#14b8a6', // teal-500
] as const;

// ── Empty state ─────────────────────────────────────────────────────

export function ReportEmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-center">
      <p className="text-sm text-text-tertiary dark:text-dark-text-tertiary">{message}</p>
    </div>
  );
}

// ── Loading state ───────────────────────────────────────────────────

export function ReportLoading({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-3 animate-pulse">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-4 bg-surface-tertiary dark:bg-dark-surface-tertiary rounded" style={{ width: `${60 + Math.random() * 40}%` }} />
      ))}
    </div>
  );
}

// ── Metric card for reports ─────────────────────────────────────────

export interface MetricCardData {
  title: string;
  value: string;
  change: string | null;
  positive: boolean;
  icon: ReactNode;
}

export function MetricCardSmall({ title, value, change, positive, icon }: MetricCardData) {
  return (
    <div className="rounded-xl bg-white dark:bg-dark-surface border border-border dark:border-dark-border p-4 shadow-sm">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-xs font-medium text-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">
            {title}
          </p>
          <p className="text-2xl font-bold text-text-primary dark:text-dark-text-primary">
            {value}
          </p>
          {change !== null && (
            <p className={`text-xs font-medium ${positive ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
              <span className="mr-1">{positive ? '▲' : '▼'}</span>
              {change}
            </p>
          )}
        </div>
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-900/30 dark:text-brand-400">
          {icon}
        </div>
      </div>
    </div>
  );
}

// ── Period comparison badge ─────────────────────────────────────────

export function PeriodComparison({ value, positive }: { value: string | null; positive: boolean }) {
  if (value === null) return null;
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium ${positive ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
      <span>{positive ? '▲' : '▼'}</span>
      {value}
    </span>
  );
}