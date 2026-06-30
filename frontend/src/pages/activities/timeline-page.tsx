import { useState, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  AlertCircle,
  History,
  ChevronDown,
  Calendar,
  CalendarPlus,
  AlertTriangle,
  ExternalLink,
} from 'lucide-react';
import { useActivityTimeline } from '../../api/activities';
import { useCalendarAuthStatus, useCalendarWatchStatus } from '../../api/sync';
import { Skeleton } from '../../components/atoms/skeleton';
import { EmptyState } from '../../components/ui/empty-state';
import { TimelineGroup, groupTimelineByDate } from './timeline-card';
import { ActivityFilters, type TimelineFilterState } from './activity-filters';
import { Button } from '../../components/atoms/button';
import { CreateCalendarEventModal } from '../../components/organisms/create-calendar-event-modal';
import type { TimelineEntry } from '../../types';

const PAGE_SIZE = 25;

function TimelineSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Skeleton variant="text" width={100} />
      </div>
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex gap-4">
          <Skeleton variant="circular" width={36} height={36} />
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

function TimelineEmptyState() {
  return (
    <EmptyState
      icon={<History className="h-8 w-8" />}
      title="No activity yet"
      description="Start by creating a deal or contacting someone — activity will appear here automatically."
    />
  );
}

function TimelineErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
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
      <Button variant="secondary" className="mt-4" onClick={onRetry}>
        Try again
      </Button>
    </div>
  );
}

export function TimelinePage() {
  const [searchParams] = useSearchParams();
  const urlActorId = searchParams.get('actor_id') || '';
  const urlEntityType = searchParams.get('entity_type') || '';
  const urlEntityId = searchParams.get('entity_id') || '';
  const [filters, setFilters] = useState<TimelineFilterState>({
    start_date: '',
    end_date: '',
    activity_type: '',
  });
  const [page, setPage] = useState(1);
  const [allEntries, setAllEntries] = useState<TimelineEntry[]>([]);
  const [hasMore, setHasMore] = useState(true);
  const [showCreateMeeting, setShowCreateMeeting] = useState(false);
  const { data: calAuth } = useCalendarAuthStatus();
  const { data: watchStatus } = useCalendarWatchStatus();

  const timelineFilters = useMemo(() => {
    const f: Record<string, string | number | undefined> = {
      page,
      page_size: PAGE_SIZE,
    };
    if (filters.start_date) f.start_date = filters.start_date;
    if (filters.end_date) f.end_date = filters.end_date;
    if (filters.activity_type) f.activity_type = filters.activity_type;
    if (urlActorId) f.actor_id = urlActorId;
    if (urlEntityType) f.entity_type = urlEntityType;
    if (urlEntityId) f.entity_id = urlEntityId;
    return f as any;
  }, [filters, page, urlActorId, urlEntityType, urlEntityId]);

  const { data, isLoading, isError, error, refetch } = useActivityTimeline(timelineFilters);

  // Accumulate entries across pages
  useMemo(() => {
    if (data?.results) {
      if (page === 1) {
        setAllEntries(data.results);
      } else {
        setAllEntries((prev) => [...prev, ...data.results]);
      }
      setHasMore(data.results.length === PAGE_SIZE);
    }
  }, [data, page]);

  // Reset when filters change
  const handleFiltersChange = (newFilters: TimelineFilterState) => {
    setFilters(newFilters);
    setPage(1);
    setAllEntries([]);
    setHasMore(true);
  };

  const handleLoadMore = () => {
    if (!isLoading && hasMore) {
      setPage((p) => p + 1);
    }
  };

  // Group by date
  const grouped = useMemo(() => groupTimelineByDate(allEntries), [allEntries]);

  return (
    <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6 lg:px-8">
      {/* Page header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-text-primary dark:text-dark-text-primary">
              Activity Timeline
            </h1>
            <p className="mt-1 text-sm text-text-secondary dark:text-dark-text-secondary">
              A reverse-chronological feed of everything happening across your organization
            </p>
          </div>
          <Button
            icon={<CalendarPlus className="h-4 w-4" />}
            onClick={() => setShowCreateMeeting(true)}
          >
            Create Meeting
          </Button>
        </div>
      </div>

      {/* Scope upgrade banner */}
      {calAuth?.connected && !watchStatus?.push_enabled && watchStatus?.connected !== false && (
        <div className="mb-4 flex items-start gap-3 rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20 px-4 py-3 text-sm">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-500 dark:text-amber-400" />
          <div className="flex-1">
            <p className="font-medium text-amber-800 dark:text-amber-200">
              Calendar Write Access Required
            </p>
            <p className="mt-0.5 text-amber-700 dark:text-amber-300">
              To create events on your Google Calendar, go to{' '}
              <a
                href="/settings"
                className="underline hover:no-underline font-medium"
              >
                Settings → Integrations
              </a>{' '}
              and reconnect your Google Calendar with write access.
            </p>
          </div>
        </div>
      )}

      {/* Push notification status */}
      {watchStatus?.push_enabled && (
        <div className="mb-4 flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-400">
          <Calendar className="h-3.5 w-3.5" />
          <span>Push notifications active</span>
          {watchStatus.last_push_received_at && (
            <span className="text-text-tertiary dark:text-dark-text-tertiary">
              · Last notification: {new Date(watchStatus.last_push_received_at).toLocaleString()}
            </span>
          )}
        </div>
      )}

      {/* Create Meeting Modal */}
      <CreateCalendarEventModal
        open={showCreateMeeting}
        onClose={() => setShowCreateMeeting(false)}
      />

      {/* Filters */}
      <div className="mb-6">
        <ActivityFilters filters={filters} onChange={handleFiltersChange} />
      </div>

      {/* URL-filtered context banner */}
      {(urlActorId || urlEntityType) && (
        <div className="mb-4 rounded-lg bg-brand-50 dark:bg-brand-900/20 border border-brand-200 dark:border-brand-800 px-4 py-2 text-sm text-brand-700 dark:text-brand-300">
          Showing activities{urlActorId ? ' for this contact' : ''}
          {urlEntityType === 'deal' ? ' for this deal' : ''}
          {urlEntityType === 'contact' ? ' for this contact' : ''}
          {' · '}
          <button
            type="button"
            onClick={() => window.history.replaceState(null, '', '/timeline')}
            className="underline hover:no-underline font-medium"
          >
            Clear filter
          </button>
        </div>
      )}

      {/* Content */}
      {isLoading && page === 1 ? (
        <TimelineSkeleton />
      ) : isError ? (
        <TimelineErrorState
          message={(error as any)?.message || 'Failed to load activity timeline'}
          onRetry={() => refetch()}
        />
      ) : allEntries.length === 0 ? (
        <TimelineEmptyState />
      ) : (
        <>
          {/* Timeline vertical line */
          allEntries.length > 0 && (
            <div className="relative">
              <div
                className="absolute left-[17px] top-0 h-full w-0.5 bg-border dark:bg-dark-border"
                aria-hidden="true"
              />
              <div className="space-y-3">
                {Array.from(grouped.entries()).map(([dateKey, entries]) => (
                  <TimelineGroup key={dateKey} dateKey={dateKey} entries={entries} />
                ))}
              </div>
            </div>
          )}

          {/* Load more */}
          {hasMore && (
            <div className="mt-8 flex justify-center">
              <Button
                variant="secondary"
                onClick={handleLoadMore}
                loading={isLoading}
                icon={isLoading ? undefined : <ChevronDown className="h-4 w-4" />}
              >
                {isLoading ? 'Loading...' : `Load more (${allEntries.length} shown)`}
              </Button>
            </div>
          )}

          {!hasMore && allEntries.length > 0 && (
            <p className="mt-6 text-center text-xs text-text-tertiary dark:text-dark-text-tertiary">
              Showing all {allEntries.length} activities
            </p>
          )}
        </>
      )}
    </div>
  );
}