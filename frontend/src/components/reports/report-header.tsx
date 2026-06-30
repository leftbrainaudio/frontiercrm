import { useState } from 'react';
import { Calendar, Filter } from 'lucide-react';
import { Button } from '../atoms/button';
import { cn } from '../../lib/utils';

export type PresetRange = '7d' | '30d' | '90d' | 'quarter' | 'custom';

const PRESETS: { key: PresetRange; label: string }[] = [
  { key: '7d', label: '7d' },
  { key: '30d', label: '30d' },
  { key: '90d', label: '90d' },
  { key: 'quarter', label: 'This Q' },
];

interface PipelineOption {
  id: string;
  name: string;
}

export interface ReportHeaderProps {
  title: string;
  preset: PresetRange;
  onPresetChange: (preset: PresetRange) => void;
  startDate: string;
  endDate: string;
  onDateChange: (start: string, end: string) => void;
  pipelineId: string | undefined;
  pipelines: PipelineOption[];
  onPipelineChange: (id: string | undefined) => void;
  groupBy: string | undefined;
  onGroupByChange: (groupBy: string | undefined) => void;
}

export function ReportHeader({
  title,
  preset,
  onPresetChange,
  startDate,
  endDate,
  onDateChange,
  pipelineId,
  pipelines,
  onPipelineChange,
  groupBy,
  onGroupByChange,
}: ReportHeaderProps) {
  const [showCustom, setShowCustom] = useState(preset === 'custom');

  const handlePreset = (key: PresetRange) => {
    onPresetChange(key);
    if (key === 'custom') {
      setShowCustom(true);
    } else {
      setShowCustom(false);
    }
  };

  return (
    <div className="sticky top-0 z-10 bg-white dark:bg-dark-surface border-b border-border dark:border-dark-border px-6 py-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-xl font-bold text-text-primary dark:text-dark-text-primary">
          {title}
        </h1>
        <div className="flex flex-wrap items-center gap-3">
          {/* Date range presets */}
          <div className="flex items-center gap-1 rounded-lg bg-surface-secondary dark:bg-dark-surface-secondary p-1">
            {PRESETS.map((p) => (
              <button
                key={p.key}
                onClick={() => handlePreset(p.key)}
                className={cn(
                  'px-3 py-1.5 text-xs font-medium rounded-md transition-colors',
                  preset === p.key
                    ? 'bg-white dark:bg-dark-surface text-brand-600 dark:text-brand-400 shadow-sm'
                    : 'text-text-secondary dark:text-dark-text-secondary hover:text-text-primary dark:hover:text-dark-text-primary',
                )}
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* Custom date range */}
          {showCustom && (
            <div className="flex items-center gap-2">
              <input
                type="date"
                value={startDate}
                onChange={(e) => onDateChange(e.target.value, endDate)}
                className="h-8 rounded-md border border-border dark:border-dark-border bg-transparent px-2 text-xs"
              />
              <span className="text-xs text-text-tertiary dark:text-dark-text-tertiary">—</span>
              <input
                type="date"
                value={endDate}
                onChange={(e) => onDateChange(startDate, e.target.value)}
                className="h-8 rounded-md border border-border dark:border-dark-border bg-transparent px-2 text-xs"
              />
            </div>
          )}

          {/* Pipeline filter */}
          <div className="flex items-center gap-1.5">
            <Filter className="h-3.5 w-3.5 text-text-tertiary dark:text-dark-text-tertiary" />
            <select
              value={pipelineId ?? ''}
              onChange={(e) => onPipelineChange(e.target.value || undefined)}
              className="h-8 rounded-md border border-border dark:border-dark-border bg-transparent px-2 text-xs"
            >
              <option value="">All Pipelines</option>
              {pipelines.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          {/* Group by */}
          <select
            value={groupBy ?? ''}
            onChange={(e) => onGroupByChange(e.target.value || undefined)}
            className="h-8 rounded-md border border-border dark:border-dark-border bg-transparent px-2 text-xs"
          >
            <option value="">Group: None</option>
            <option value="owner">Group: Owner</option>
          </select>
        </div>
      </div>
    </div>
  );
}