import { useState } from 'react';
import { Calendar, Filter, X } from 'lucide-react';
import { cn } from '../../lib/utils';
import { Button } from '../../components/atoms/button';

export interface TimelineFilterState {
  start_date: string;
  end_date: string;
  activity_type: string;
}

interface ActivityTypeOption {
  value: string;
  label: string;
  color: string;
}

const ACTIVITY_TYPES: ActivityTypeOption[] = [
  { value: '', label: 'All types', color: '' },
  { value: 'note', label: 'Notes', color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40' },
  { value: 'call', label: 'Calls', color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40' },
  { value: 'email', label: 'Emails', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40' },
  { value: 'meeting', label: 'Meetings', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40' },
  { value: 'task', label: 'Tasks', color: 'bg-rose-100 text-rose-700 dark:bg-rose-900/40' },
  { value: 'deal_stage_change', label: 'Deal changes', color: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40' },
  { value: 'file_upload', label: 'File uploads', color: 'bg-sky-100 text-sky-700 dark:bg-sky-900/40' },
  { value: 'system', label: 'System', color: 'bg-gray-100 text-gray-700 dark:bg-gray-800' },
];

interface DatePreset {
  label: string;
  days: number;
}

const DATE_PRESETS: DatePreset[] = [
  { label: 'Today', days: 0 },
  { label: 'This week', days: 7 },
  { label: 'This month', days: 30 },
  { label: 'Last 90 days', days: 90 },
];

interface ActivityFiltersProps {
  filters: TimelineFilterState;
  onChange: (filters: TimelineFilterState) => void;
  showDatePicker?: boolean;
}

export function ActivityFilters({ filters, onChange, showDatePicker = false }: ActivityFiltersProps) {
  const [showMobile, setShowMobile] = useState(false);

  const handleTypeChange = (value: string) => {
    onChange({ ...filters, activity_type: value });
  };

  const handlePreset = (days: number) => {
    const end = new Date().toISOString().slice(0, 10);
    const start = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
    onChange({ ...filters, start_date: days === 0 ? end : start, end_date: end });
  };

  const clearFilters = () => {
    onChange({ start_date: '', end_date: '', activity_type: '' });
  };

  const hasActiveFilters = filters.start_date || filters.end_date || filters.activity_type;

  return (
    <div>
      {/* Mobile toggle */}
      <div className="flex items-center justify-between lg:hidden">
        <Button
          variant="secondary"
          size="sm"
          icon={<Filter className="h-4 w-4" />}
          onClick={() => setShowMobile(!showMobile)}
        >
          Filters {hasActiveFilters ? '(active)' : ''}
        </Button>
        {hasActiveFilters && (
          <button
            type="button"
            onClick={clearFilters}
            className="text-xs text-brand-600 hover:text-brand-700 dark:text-brand-400"
          >
            Clear all
          </button>
        )}
      </div>

      <div className={cn('space-y-4', showMobile ? 'mt-4' : 'hidden lg:block')}>
        {/* Activity type pills */}
        <div className="flex flex-wrap gap-2">
          {ACTIVITY_TYPES.map((t) => (
            <button
              key={t.value}
              type="button"
              onClick={() => handleTypeChange(t.value)}
              className={cn(
                'rounded-full px-3.5 py-1.5 text-xs font-medium transition-colors',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
                filters.activity_type === t.value
                  ? 'bg-brand-600 text-white dark:bg-brand-500'
                  : 'bg-surface-secondary text-text-secondary hover:bg-surface-tertiary dark:bg-dark-surface-secondary dark:text-dark-text-secondary dark:hover:bg-dark-surface-tertiary',
              )}
              aria-pressed={filters.activity_type === t.value}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Date presets */}
        <div className="flex flex-wrap items-center gap-2">
          <Calendar className="h-4 w-4 text-text-tertiary dark:text-dark-text-tertiary" />
          <span className="text-xs font-medium text-text-tertiary dark:text-dark-text-tertiary mr-1">
            Date:
          </span>
          {DATE_PRESETS.map((p) => (
            <button
              key={p.days}
              type="button"
              onClick={() => handlePreset(p.days)}
              className={cn(
                'rounded-md px-2.5 py-1 text-xs font-medium transition-colors',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
                !filters.start_date && !filters.end_date && p.days === 7
                  ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400'
                  : 'bg-surface-secondary text-text-secondary hover:bg-surface-tertiary dark:bg-dark-surface-secondary dark:text-dark-text-secondary dark:hover:bg-dark-surface-tertiary',
              )}
            >
              {p.label}
            </button>
          ))}
        </div>

        {/* Action: clear */}
        {hasActiveFilters && (
          <button
            type="button"
            onClick={clearFilters}
            className="hidden lg:inline-flex items-center gap-1 text-xs text-brand-600 hover:text-brand-700 dark:text-brand-400 transition-colors"
          >
            <X className="h-3 w-3" />
            Clear all filters
          </button>
        )}
      </div>
    </div>
  );
}