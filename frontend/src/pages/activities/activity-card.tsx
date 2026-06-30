import type { ReactNode } from 'react';
import {
  FileText,
  Phone,
  Mail,
  Calendar,
  CheckSquare,
  TrendingUp,
  Inbox,
  ArrowUpRight,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { Card } from '../../components/molecules/card';
import { Avatar } from '../../components/atoms/avatar';
import { cn } from '../../lib/utils';
import type { TimelineEntry } from '../../types';

export const ACTIVITY_ICONS: Record<string, ReactNode> = {
  note: <FileText className="h-4 w-4" />,
  call: <Phone className="h-4 w-4" />,
  email: <Mail className="h-4 w-4" />,
  meeting: <Calendar className="h-4 w-4" />,
  task: <CheckSquare className="h-4 w-4" />,
  deal: <TrendingUp className="h-4 w-4" />,
  deal_stage_change: <TrendingUp className="h-4 w-4" />,
  deal_status_change: <TrendingUp className="h-4 w-4" />,
  file_upload: <FileText className="h-4 w-4" />,
  system: <Inbox className="h-4 w-4" />,
};

export const ACTIVITY_COLORS: Record<string, string> = {
  note: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  call: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
  email: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  meeting: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
  task: 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300',
  deal: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-300',
  deal_stage_change: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-300',
  deal_status_change: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-300',
  file_upload: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300',
};

interface ActivityCardProps {
  activity: TimelineEntry;
}

export function ActivityCard({ activity }: ActivityCardProps) {
  const icon = ACTIVITY_ICONS[activity.activity_type] || <Inbox className="h-4 w-4" />;
  const colorClass =
    ACTIVITY_COLORS[activity.activity_type] ||
    'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400';

  return (
    <div className="relative flex gap-4 pb-8 last:pb-0">
      {/* Icon circle */}
      <div className="relative z-10 flex shrink-0">
        <div
          className={cn('flex h-9 w-9 items-center justify-center rounded-full', colorClass)}
        >
          {icon}
        </div>
      </div>

      {/* Activity card */}
      <div className="min-w-0 flex-1">
        <Card padding="sm" className="group">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <h4 className="truncate text-sm font-medium text-text-primary dark:text-dark-text-primary">
                {activity.title ||
                  `${activity.activity_type.replace(/_/g, ' ')} activity`}
              </h4>
              {activity.description && (
                <p className="mt-1 line-clamp-2 whitespace-pre-wrap text-sm text-text-secondary dark:text-dark-text-secondary">
                  {activity.description}
                </p>
              )}
              <div className="mt-2 flex items-center gap-3 text-xs text-text-tertiary dark:text-dark-text-tertiary">
                <time dateTime={activity.created_at}>
                  {formatDistanceToNow(new Date(activity.created_at), { addSuffix: true })}
                </time>

                {activity.actor.name && (
                  <span className="flex items-center gap-1.5">
                    <Avatar size="xs" fallback={activity.actor.name.charAt(0).toUpperCase()} />
                    <span>{activity.actor.name}</span>
                  </span>
                )}
              </div>
            </div>

            {activity.entity.name && (
              <a
                href={activity.entity.url || '#'}
                className="flex shrink-0 items-center gap-1 rounded-md border border-border px-2 py-1 text-xs text-text-secondary hover:bg-surface-secondary dark:border-dark-border dark:text-dark-text-secondary dark:hover:bg-dark-surface-secondary"
              >
                {activity.entity.name}
                <ArrowUpRight className="h-3 w-3" />
              </a>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}