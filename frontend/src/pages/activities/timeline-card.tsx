import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Phone,
  Mail,
  Calendar,
  CheckSquare,
  TrendingUp,
  Inbox,
  Upload,
  ExternalLink,
  Edit3,
} from 'lucide-react';
import { format, parseISO } from 'date-fns';
import type { LucideProps } from 'lucide-react';
import type { TimelineEntry } from '../../types';
import { Avatar } from '../../components/atoms/avatar';
import { Card } from '../../components/molecules/card';
import { cn } from '../../lib/utils';

interface ActivityIconMap {
  icon: React.ComponentType<LucideProps>;
  color: string;
}

const ACTIVITY_STYLES: Record<string, ActivityIconMap> = {
  note: { icon: FileText, color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300' },
  call: { icon: Phone, color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300' },
  email: { icon: Mail, color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300' },
  meeting: { icon: Calendar, color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300' },
  task: { icon: CheckSquare, color: 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300' },
  deal_stage_change: { icon: TrendingUp, color: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-300' },
  deal_status_change: { icon: TrendingUp, color: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300' },
  file_upload: { icon: Upload, color: 'bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300' },
  system: { icon: Inbox, color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' },
};

const DEFAULT_STYLE: ActivityIconMap = { icon: Inbox, color: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400' };

function formatActivityTime(dateStr: string): string {
  const date = parseISO(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
  if (diffMins < 10080) return `${Math.floor(diffMins / 1440)}d ago`;
  return format(date, 'MMM d, yyyy');
}

export function groupTimelineByDate(entries: TimelineEntry[]): Map<string, TimelineEntry[]> {
  const groups = new Map<string, TimelineEntry[]>();
  for (const entry of entries) {
    const dateKey = entry.created_at.slice(0, 10); // YYYY-MM-DD
    const existing = groups.get(dateKey) ?? [];
    existing.push(entry);
    groups.set(dateKey, existing);
  }
  return groups;
}

function getDateLabel(dateKey: string): string {
  const date = parseISO(dateKey);
  const now = new Date();
  const today = now.toISOString().slice(0, 10);
  const yesterday = new Date(now.getTime() - 86400000).toISOString().slice(0, 10);

  if (dateKey === today) return 'Today';
  if (dateKey === yesterday) return 'Yesterday';
  return format(date, 'EEEE, MMMM d, yyyy');
}

export function TimelineCard({ entry }: { entry: TimelineEntry }) {
  const navigate = useNavigate();
  const style = ACTIVITY_STYLES[entry.activity_type] ?? DEFAULT_STYLE;
  const Icon = style.icon;

  const handleEntityClick = () => {
    if (entry.entity.url) {
      navigate(entry.entity.url);
    }
  };

  return (
    <div className="relative flex gap-4 pb-6 last:pb-0">
      {/* Timeline dot line */}
      <div className="relative z-10 flex shrink-0 flex-col items-center">
        <div className={cn('flex h-9 w-9 items-center justify-center rounded-full', style.color)}>
          <Icon className="h-4 w-4" />
        </div>
      </div>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <Card padding="sm" variant="outline" className="transition-shadow hover:shadow-sm">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <h4 className="text-sm font-medium text-text-primary dark:text-dark-text-primary">
                {entry.title || `${entry.activity_type.replace(/_/g, ' ')} activity`}
              </h4>
              {entry.description && (
                <p className="mt-1 text-sm text-text-secondary dark:text-dark-text-secondary line-clamp-2 whitespace-pre-wrap">
                  {entry.description}
                </p>
              )}
              <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-text-tertiary dark:text-dark-text-tertiary">
                <time dateTime={entry.created_at}>
                  {formatActivityTime(entry.created_at)}
                </time>
                <span className="flex items-center gap-1.5">
                  <Avatar size="xs" fallback={entry.actor.name || '?'} src={entry.actor.avatar_url || undefined} />
                  <span className="truncate max-w-[120px]">{entry.actor.name || 'Unknown'}</span>
                </span>

                {/* Event source indicator for meetings */}
                {entry.activity_type === 'meeting' && entry.metadata?.event_source === 'crm' && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-brand-50 dark:bg-brand-900/20 px-2 py-0.5 text-[11px] font-medium text-brand-600 dark:text-brand-400">
                    <Edit3 className="h-3 w-3" />
                    Created in FrontierCRM
                  </span>
                )}
                {entry.activity_type === 'meeting' && entry.metadata?.event_source === 'google' && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 dark:bg-blue-900/20 px-2 py-0.5 text-[11px] font-medium text-blue-600 dark:text-blue-400">
                    <ExternalLink className="h-3 w-3" />
                    Synced from Google Calendar
                  </span>
                )}

                {entry.entity.name && (
                  <button
                    type="button"
                    onClick={handleEntityClick}
                    className="truncate max-w-[180px] text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300 transition-colors hover:underline"
                  >
                    {entry.entity.name}
                  </button>
                )}
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

export function TimelineGroup({
  dateKey,
  entries,
}: {
  dateKey: string;
  entries: TimelineEntry[];
}) {
  return (
    <div>
      <div className="sticky top-0 z-20 mb-3 -ml-1">
        <span className="inline-flex items-center rounded-full bg-surface-secondary dark:bg-dark-surface-secondary px-3 py-1 text-xs font-semibold text-text-secondary dark:text-dark-text-secondary">
          {getDateLabel(dateKey)}
        </span>
      </div>
      {entries.map((entry) => (
        <TimelineCard key={entry.id} entry={entry} />
      ))}
    </div>
  );
}