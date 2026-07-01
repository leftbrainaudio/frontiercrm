import { useNavigate } from 'react-router-dom';
import {
  DollarSign,
  Target,
  TrendingUp,
  Briefcase,
  Activity,
  ClipboardList,
  ArrowRight,
  BarChart3,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { Card } from '../../components/molecules/card';
import { Skeleton } from '../../components/atoms/skeleton';
import { Badge } from '../../components/atoms/badge';
import { Avatar } from '../../components/atoms/avatar';
import { Button } from '../../components/atoms/button';
import { useDashboardReport, useStaleDeals } from '../../api/reports';
import { useActivityTimeline } from '../../api/activities';
import { useTasks } from '../../api/tasks';
import { cn } from '../../lib/utils';
import type { TimelineEntry } from '../../types';

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

interface MetricCardProps {
  title: string;
  value: string;
  icon: React.ReactNode;
  trend?: { value: string; positive: boolean };
  loading?: boolean;
}

function MetricCard({ title, value, icon, trend, loading }: MetricCardProps) {
  const isZero = value === '$0' || value === '0%' || value === '0';
  return (
    <Card className="relative overflow-hidden">
      {loading ? (
        <div className="space-y-3">
          <Skeleton variant="text" width="60%" />
          <Skeleton variant="text" width="40%" height={32} />
          {trend && <Skeleton variant="text" width="30%" />}
        </div>
      ) : (
        <>
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-text-secondary dark:text-dark-text-secondary">
                {title}
              </p>
              {isZero ? (
                <span className="inline-flex items-center rounded-full bg-gray-100 dark:bg-gray-800 px-2.5 py-0.5 text-xs font-medium text-text-tertiary dark:text-dark-text-tertiary">
                  No data
                </span>
              ) : (
                <p className="text-2xl font-bold text-text-primary dark:text-dark-text-primary">
                  {value}
                </p>
              )}
            </div>
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-900/30 dark:text-brand-400">
              {icon}
            </div>
          </div>
          {!isZero && trend && (
            <div className="mt-3 flex items-center gap-1.5">
              <span
                className={cn(
                  'text-xs font-medium',
                  trend.positive
                    ? 'text-emerald-600 dark:text-emerald-400'
                    : 'text-red-600 dark:text-red-400',
                )}
              >
                {trend.value}
              </span>
              <span className="text-xs text-text-tertiary dark:text-dark-text-tertiary">
                vs last month
              </span>
            </div>
          )}
        </>
      )}
    </Card>
  );
}

function ActivityEmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-center">
      <div className="relative mb-4 h-20 w-full max-w-[200px]">
        <svg viewBox="0 0 200 60" className="h-full w-full" aria-hidden="true">
          <path
            d="M0 50 Q20 35 40 45 Q60 55 80 40 Q100 25 120 38 Q140 50 160 35 Q180 20 200 30"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className="text-gray-200 dark:text-slate-700"
          />
          <circle cx="160" cy="35" r="3" className="fill-brand-400" />
          <circle cx="120" cy="38" r="2" className="fill-gray-300 dark:fill-slate-600" />
          <circle cx="40" cy="45" r="2" className="fill-gray-300 dark:fill-slate-600" />
        </svg>
      </div>
      <Badge variant="neutral" size="sm">No recent activity</Badge>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-surface-secondary dark:bg-dark-surface-secondary">
        <Activity className="h-6 w-6 text-text-tertiary dark:text-dark-text-tertiary" />
      </div>
      <p className="text-sm text-text-tertiary dark:text-dark-text-tertiary">
        {message}
      </p>
    </div>
  );
}

function ActivityItem({
  title,
  type,
  actorName,
  time,
  entityName,
  onEntityClick,
}: {
  title: string;
  type: string;
  actorName?: string;
  time: string;
  entityName?: string;
  onEntityClick?: () => void;
}) {
  const typeIcon: Record<string, string> = {
    note: '📝',
    call: '📞',
    email: '📧',
    meeting: '📅',
    task: '✅',
    deal_stage_change: '🔄',
    deal_status_change: '🏆',
    file_upload: '📎',
    system: '⚙️',
  };

  const icon = typeIcon[type] ?? <Activity className="h-4 w-4" />;

  return (
    <div className="flex items-start gap-3 py-2.5">
      <span className="mt-0.5 text-base" role="img" aria-label={type}>
        {icon}
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm text-text-primary dark:text-dark-text-primary">
          {title}
        </p>
        <div className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-text-tertiary dark:text-dark-text-tertiary">
          <span>{time}</span>
          {actorName && <span>· {actorName}</span>}
          {entityName && (
            <button
              type="button"
              onClick={onEntityClick}
              className="truncate max-w-[120px] text-brand-600 hover:text-brand-700 dark:text-brand-400 transition-colors hover:underline"
            >
              · {entityName}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function TaskItem({
  title,
  priority,
  dueAt,
}: {
  title: string;
  priority: string;
  dueAt: string | null;
}) {
  const priorityColor: Record<string, string> = {
    urgent: 'bg-red-500',
    high: 'bg-amber-500',
    medium: 'bg-blue-500',
    low: 'bg-gray-400',
  };

  const formatDue = (date: string | null) => {
    if (!date) return 'No due date';
    const d = new Date(date);
    const now = new Date();
    const diff = d.getTime() - now.getTime();
    const days = Math.ceil(diff / (1000 * 60 * 60 * 24));
    if (days < 0) return `${Math.abs(days)}d overdue`;
    if (days === 0) return 'Due today';
    if (days === 1) return 'Due tomorrow';
    return `Due in ${days}d`;
  };

  return (
    <div className="flex items-start gap-3 py-2.5">
      <span
        className={cn(
          'mt-1.5 h-2 w-2 shrink-0 rounded-full',
          priorityColor[priority] ?? 'bg-gray-400',
        )}
      />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm text-text-primary dark:text-dark-text-primary">
          {title}
        </p>
        <p className="mt-0.5 text-xs text-text-tertiary dark:text-dark-text-tertiary">
          {formatDue(dueAt)}
        </p>
      </div>
      <Badge variant={priority === 'urgent' ? 'danger' : 'warning'} size="sm">
        {priority}
      </Badge>
    </div>
  );
}

export function DashboardPage() {
  const navigate = useNavigate();

  // Use the server-side report endpoint instead of client-side computation
  const { data: report, isLoading: reportLoading } = useDashboardReport({
    start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10),
    end_date: new Date().toISOString().slice(0, 10),
  });
  const { data: staleDeals } = useStaleDeals({ days_since_activity: '14', limit: '5' });
  const { data: timelineData, isLoading: activitiesLoading } = useActivityTimeline({
    page_size: 10,
  });
  const { data: tasksData, isLoading: tasksLoading } = useTasks({ page_size: '5' });

  const isLoading = reportLoading;

  const hasStaleDeals = staleDeals?.stale_deals && staleDeals.stale_deals.length > 0;

  const chartData =
    report?.deals_by_stage?.map((s) => ({
      name: s.stage_name,
      value: s.value,
      count: s.count,
    })) ?? [];

  const hasDeals = report && report.summary.active_deals > 0;
  const activities = timelineData?.results ?? [];
  const tasks = tasksData?.results ?? [];

  const noReportData = !isLoading && (!report || report.summary.active_deals === 0);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-brand-600 to-brand-800 px-6 py-8 sm:px-8">
        <div className="relative z-10">
          <h1 className="text-2xl font-bold text-white sm:text-3xl">
            Dashboard
          </h1>
          <p className="mt-1 text-sm text-brand-100">
            Welcome back! Here&apos;s your pipeline overview.
          </p>
        </div>
        <div className="absolute right-0 top-0 h-full w-1/3 opacity-10">
          <div className="h-full w-full bg-[radial-gradient(ellipse_at_top_right,_white_0%,_transparent_70%)]" />
        </div>
      </div>

      {/* Stale Deals Warning Banner */}
      {hasStaleDeals && (
        <div className="flex items-center gap-3 rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 px-4 py-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/50">
            <BarChart3 className="h-4 w-4 text-red-600 dark:text-red-400" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-red-800 dark:text-red-300">
              {staleDeals!.stale_deals.length} deal{staleDeals!.stale_deals.length !== 1 ? 's' : ''} need{staleDeals!.stale_deals.length === 1 ? 's' : ''} attention
            </p>
            <p className="text-xs text-red-600 dark:text-red-400">
              {staleDeals!.stale_deals.filter((d) => d.is_overdue).length} overdue · View in Reports for details
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/reports')}
          >
            View Reports
          </Button>
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Total Pipeline Value"
          value={isLoading ? '' : formatCurrency(report?.summary.total_pipeline_value ?? 0)}
          icon={<DollarSign className="h-5 w-5" />}
          trend={
            report?.summary.pipeline_value_change != null
              ? {
                  value: `${report.summary.pipeline_value_change >= 0 ? '+' : ''}${report.summary.pipeline_value_change.toFixed(1)}%`,
                  positive: report.summary.pipeline_value_change >= 0,
                }
              : undefined
          }
          loading={isLoading}
          noData={noReportData}
        />
        <MetricCard
          title="Won Deals"
          value={isLoading ? '' : formatCurrency(report?.summary.won_value ?? 0)}
          icon={<Target className="h-5 w-5" />}
          trend={
            report?.summary.won_value_change != null
              ? {
                  value: `${report.summary.won_value_change >= 0 ? '+' : ''}${report.summary.won_value_change.toFixed(1)}%`,
                  positive: report.summary.won_value_change >= 0,
                }
              : undefined
          }
          loading={isLoading}
          noData={noReportData}
        />
        <MetricCard
          title="Win Rate"
          value={isLoading ? '' : formatPercent(report?.summary.win_rate ?? 0)}
          icon={<TrendingUp className="h-5 w-5" />}
          trend={
            report?.summary.win_rate_change != null
              ? {
                  value: `${report.summary.win_rate_change >= 0 ? '+' : ''}${report.summary.win_rate_change.toFixed(1)}pp`,
                  positive: report.summary.win_rate_change >= 0,
                }
              : undefined
          }
          loading={isLoading}
          noData={noReportData}
        />
        <MetricCard
          title="Active Deals"
          value={isLoading ? '' : String(report?.summary.active_deals ?? 0)}
          icon={<Briefcase className="h-5 w-5" />}
          trend={
            report?.summary.active_deals_change != null
              ? {
                  value: `${report.summary.active_deals_change >= 0 ? '+' : ''}${report.summary.active_deals_change}`,
                  positive: report.summary.active_deals_change >= 0,
                }
              : undefined
          }
          loading={isLoading}
          noData={noReportData}
        />
      </div>

      {/* Charts + Sidebar */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Pipeline by Stage Chart */}
        <Card
          title="Pipeline by Stage"
          subtitle="Deal value distribution across stages"
          className="lg:col-span-2"
        >
          {isLoading ? (
            <div className="space-y-3">
              <Skeleton variant="rectangular" height={240} />
            </div>
          ) : !hasDeals ? (
            <EmptyState message="No pipeline data yet" />
          ) : (
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 8, right: 8, left: -8, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border dark:stroke-dark-border" />
                  <XAxis
                    dataKey="name"
                    tick={{ fontSize: 12 }}
                    className="text-text-tertiary dark:text-dark-text-tertiary"
                  />
                  <YAxis
                    tick={{ fontSize: 12 }}
                    className="text-text-tertiary dark:text-dark-text-tertiary"
                    tickFormatter={(v: number) =>
                      v >= 1000 ? `$${(v / 1000).toFixed(0)}k` : `$${v}`
                    }
                  />
                  <Tooltip
                    contentStyle={{
                      borderRadius: '8px',
                      border: '1px solid var(--color-border)',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                      fontSize: '13px',
                    }}
                    formatter={(value: number) => [formatCurrency(value), 'Value']}
                  />
                  <Bar
                    dataKey="value"
                    fill="var(--color-brand-500, #3B82F6)"
                    radius={[4, 4, 0, 0]}
                    maxBarSize={48}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>

        {/* Right sidebar: Activities + Tasks */}
        <div className="space-y-6">
          {/* Recent Activity */}
          <Card title="Recent Activity" subtitle="Latest actions on the pipeline">
            {activitiesLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <Skeleton variant="circular" width={20} height={20} />
                    <div className="flex-1 space-y-1.5">
                      <Skeleton variant="text" width="70%" />
                      <Skeleton variant="text" width="40%" />
                    </div>
                  </div>
                ))}
              </div>
            ) : activities.length === 0 ? (
              <ActivityEmptyState />
            ) : (
              <div className="divide-y divide-border dark:divide-dark-border">
                {activities.map((activity: TimelineEntry) => (
                  <ActivityItem
                    key={activity.id}
                    title={activity.title}
                    type={activity.activity_type}
                    actorName={activity.actor?.name}
                    time={formatRelativeTime(activity.created_at)}
                    entityName={activity.entity?.name}
                    onEntityClick={() => activity.entity?.url && navigate(activity.entity.url)}
                  />
                ))}
              </div>
            )}
            {activities.length > 0 && (
              <div className="mt-2 border-t border-border dark:border-dark-border pt-2 text-center">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigate('/timeline')}
                >
                  View full timeline →
                </Button>
              </div>
            )}
          </Card>

          {/* Tasks Due */}
          <Card title="Tasks Due" subtitle="Upcoming and overdue tasks">
            {tasksLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <Skeleton variant="circular" width={8} height={8} />
                    <div className="flex-1 space-y-1.5">
                      <Skeleton variant="text" width="70%" />
                      <Skeleton variant="text" width="40%" />
                    </div>
                  </div>
                ))}
              </div>
            ) : tasks.length === 0 ? (
              <EmptyState message="No tasks due" />
            ) : (
              <div className="divide-y divide-border dark:divide-dark-border">
                {tasks.map((task) => (
                  <TaskItem
                    key={task.id}
                    title={task.title}
                    priority={task.priority}
                    dueAt={task.due_at}
                  />
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="flex flex-wrap items-center gap-2 sm:gap-3">
        <Button
          variant="secondary"
          icon={<ClipboardList className="h-4 w-4" />}
          onClick={() => navigate('/contacts')}
        >
          View Contacts
        </Button>
        <Button
          variant="secondary"
          icon={<ArrowRight className="h-4 w-4" />}
          onClick={() => navigate('/pipeline')}
        >
          View Pipeline
        </Button>
        <Button
          icon={<BarChart3 className="h-4 w-4" />}
          onClick={() => navigate('/reports')}
        >
          View Full Reports
        </Button>
      </div>
    </div>
  );
}

function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}