import { useState, type ReactNode } from 'react';
import {
  FileText,
  Phone,
  Mail,
  Calendar,
  CheckSquare,
  TrendingUp,
  Plus,
  AlertCircle,
  Inbox,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useActivities, useCreateActivity } from '../../api/activities';
import { Button } from '../../components/ui/button';
import { Card } from '../../components/ui/card';
import { Modal } from '../../components/ui/modal';
import { Input } from '../../components/ui/input';
import { Skeleton } from '../../components/ui/skeleton';
import { Avatar } from '../../components/ui/avatar';
import { cn } from '../../lib/utils';
import type { ActivityType } from '../../types';

type ActivityFilter = 'all' | 'note' | 'call' | 'email' | 'meeting' | 'task' | 'deal';

const FILTERS: { key: ActivityFilter; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'note', label: 'Notes' },
  { key: 'call', label: 'Calls' },
  { key: 'email', label: 'Emails' },
  { key: 'meeting', label: 'Meetings' },
  { key: 'task', label: 'Tasks' },
  { key: 'deal', label: 'Deals' },
];

const ACTIVITY_ICONS: Record<string, ReactNode> = {
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

const ACTIVITY_COLORS: Record<string, string> = {
  note: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  call: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
  email: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  meeting: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
  task: 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300',
  deal: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-300',
};

function mapFilterToActivityType(filter: ActivityFilter): ActivityType | undefined {
  if (filter === 'all') return undefined;
  const mapping: Record<string, ActivityType> = {
    note: 'note',
    call: 'call',
    email: 'email',
    meeting: 'meeting',
    task: 'task',
    deal: 'deal_stage_change',
  };
  return mapping[filter] as ActivityType;
}

function getActorInitials(activity: { actor_id?: string | null; title?: string }): string {
  if (activity.actor_id) {
    return activity.actor_id.slice(0, 2).toUpperCase();
  }
  return '?';
}

function TimelineSkeleton() {
  return (
    <div className="space-y-6">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex gap-4">
          <div className="flex flex-col items-center">
            <Skeleton variant="circular" width={36} height={36} />
            {i < 4 && <div className="mt-1 w-px flex-1 bg-border dark:bg-dark-border" />}
          </div>
          <div className="flex-1 space-y-2 pb-6">
            <Skeleton width="60%" height={16} />
            <Skeleton count={2} />
            <Skeleton width="30%" height={12} />
          </div>
        </div>
      ))}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-surface-secondary dark:bg-dark-surface-secondary">
        <Inbox className="h-8 w-8 text-text-tertiary dark:text-dark-text-tertiary" />
      </div>
      <h3 className="text-lg font-semibold text-text-primary dark:text-dark-text-primary">
        No activities yet
      </h3>
      <p className="mt-1 text-sm text-text-secondary dark:text-dark-text-secondary max-w-sm">
        Activity tracking helps you stay on top of your interactions. Start by adding a note or logging a call.
      </p>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-50 dark:bg-red-900/20">
        <AlertCircle className="h-8 w-8 text-red-500 dark:text-red-400" />
      </div>
      <h3 className="text-lg font-semibold text-text-primary dark:text-dark-text-primary">
        Something went wrong
      </h3>
      <p className="mt-1 text-sm text-text-secondary dark:text-dark-text-secondary max-w-sm">
        {message}
      </p>
      <Button variant="secondary" className="mt-4" onClick={() => window.location.reload()}>
        Try again
      </Button>
    </div>
  );
}

export function ActivityPage() {
  const [activeFilter, setActiveFilter] = useState<ActivityFilter>('all');
  const [addNoteOpen, setAddNoteOpen] = useState(false);
  const [noteContent, setNoteContent] = useState('');
  const [noteEntityType, setNoteEntityType] = useState('');
  const [noteEntityId, setNoteEntityId] = useState('');

  const activityTypeParam = mapFilterToActivityType(activeFilter);
  const params = activityTypeParam ? { activity_type: activityTypeParam } : undefined;
  const { data, isLoading, isError, error } = useActivities(params);
  const createActivity = useCreateActivity();

  const activities = data?.results ?? [];

  const handleAddNote = async () => {
    if (!noteContent.trim()) return;
    try {
      await createActivity.mutateAsync({
        activity_type: 'note',
        title: noteContent.split('\n')[0].slice(0, 100),
        description: noteContent,
        entity_type: noteEntityType || undefined,
        entity_id: noteEntityId || undefined,
      } as any);
      setNoteContent('');
      setNoteEntityType('');
      setNoteEntityId('');
      setAddNoteOpen(false);
    } catch {
      // error handled by toast in production
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6 lg:px-8">
      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-text-primary dark:text-dark-text-primary">
          Activity Feed
        </h1>
        <p className="mt-1 text-sm text-text-secondary dark:text-dark-text-secondary">
          A unified timeline of all your team&apos;s activities
        </p>
      </div>

      {/* Filter buttons */}
      <div className="mb-6 flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            type="button"
            onClick={() => setActiveFilter(f.key)}
            className={cn(
              'rounded-full px-4 py-1.5 text-sm font-medium transition-colors',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
              activeFilter === f.key
                ? 'bg-brand-600 text-white dark:bg-brand-500'
                : 'bg-surface-secondary text-text-secondary hover:bg-surface-tertiary dark:bg-dark-surface-secondary dark:text-dark-text-secondary dark:hover:bg-dark-surface-tertiary',
            )}
            aria-pressed={activeFilter === f.key}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {isLoading ? (
        <TimelineSkeleton />
      ) : isError ? (
        <ErrorState message={(error as any)?.message || 'Failed to load activities'} />
      ) : activities.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="relative">
          {/* Vertical timeline line */}
          <div className="absolute left-[17px] top-0 h-full w-0.5 bg-border dark:bg-dark-border" aria-hidden="true" />

          <div className="space-y-0">
            {activities.map((activity) => (
              <div key={activity.id} className="relative flex gap-4 pb-8 last:pb-0">
                {/* Icon circle */}
                <div className="relative z-10 flex shrink-0">
                  <div
                    className={cn(
                      'flex h-9 w-9 items-center justify-center rounded-full',
                      ACTIVITY_COLORS[activity.activity_type] ||
                        'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
                    )}
                  >
                    {ACTIVITY_ICONS[activity.activity_type] || <Inbox className="h-4 w-4" />}
                  </div>
                </div>

                {/* Activity card */}
                <div className="flex-1 min-w-0">
                  <Card padding="sm" className="group">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <h4 className="text-sm font-medium text-text-primary dark:text-dark-text-primary truncate">
                          {activity.title || `${activity.activity_type.replace(/_/g, ' ')} activity`}
                        </h4>
                        {activity.description && (
                          <p className="mt-1 text-sm text-text-secondary dark:text-dark-text-secondary line-clamp-2 whitespace-pre-wrap">
                            {activity.description}
                          </p>
                        )}
                        <div className="mt-2 flex items-center gap-3 text-xs text-text-tertiary dark:text-dark-text-tertiary">
                          <time dateTime={activity.created_at}>
                            {formatDistanceToNow(new Date(activity.created_at), { addSuffix: true })}
                          </time>
                          {activity.actor_id && (
                            <span className="flex items-center gap-1.5">
                              <Avatar size="xs" fallback={getActorInitials(activity)} />
                              <span>{activity.actor_id}</span>
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </Card>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Floating Add Note button */}
      <button
        type="button"
        onClick={() => setAddNoteOpen(true)}
        className={cn(
          'fixed bottom-6 right-6 z-40 flex h-14 w-14 items-center justify-center rounded-full shadow-lg',
          'bg-brand-600 text-white hover:bg-brand-700',
          'dark:bg-brand-500 dark:hover:bg-brand-600',
          'transition-all duration-200 hover:scale-105 active:scale-95',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2',
        )}
        aria-label="Add Note"
      >
        <Plus className="h-6 w-6" />
      </button>

      {/* Add Note Modal */}
      <Modal
        open={addNoteOpen}
        onClose={() => setAddNoteOpen(false)}
        title="Add Note"
        size="md"
        footer={
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setAddNoteOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddNote} loading={createActivity.isPending} disabled={!noteContent.trim()}>
              Save Note
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <div>
            <label
              htmlFor="note-content"
              className="mb-1.5 block text-sm font-medium text-text-primary dark:text-dark-text-primary"
            >
              Note
            </label>
            <textarea
              id="note-content"
              value={noteContent}
              onChange={(e) => setNoteContent(e.target.value)}
              rows={5}
              className="w-full rounded-lg border border-border bg-white px-3 py-2 text-sm text-text-primary placeholder:text-text-tertiary focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary dark:placeholder:text-dark-text-tertiary dark:focus:border-brand-400"
              placeholder="What happened?"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Entity Type (optional)"
              value={noteEntityType}
              onChange={(e) => setNoteEntityType(e.target.value)}
              placeholder="e.g. contact, deal"
            />
            <Input
              label="Entity ID (optional)"
              value={noteEntityId}
              onChange={(e) => setNoteEntityId(e.target.value)}
              placeholder="Entity ID"
            />
          </div>
        </div>
      </Modal>
    </div>
  );
}