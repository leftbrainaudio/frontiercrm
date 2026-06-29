import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  DollarSign,
  Target,
  TrendingUp,
  Briefcase,
  Activity,
  ClipboardList,
  ArrowRight,
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
import { Card } from '../../components/ui/card';
import { Skeleton } from '../../components/ui/skeleton';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { usePipelines, useDeals } from '../../api/deals';
import { useActivities } from '../../api/activities';
import { useTasks } from '../../api/tasks';
import { cn } from '../../lib/utils';
import type { Deal } from '../../types';

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
              <p className="text-2xl font-bold text-text-primary dark:text-dark-text-primary">
                {value}
              </p>
            </div>
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-900/30 dark:text-brand-400">
              {icon}
            </div>
          </div>
          {trend && (
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
  time,
}: {
  title: string;
  type: string;
  time: string;
}) {
  const typeIcon = {
    note: '📝',
    call: '📞',
    email: '📧',
    meeting: '📅',
    task: '✅',
    deal_stage_change: '🔄',
    deal_status_change: '🏆',
    file_upload: '📎',
    system: '⚙️',
  } as const;

  const icon =
    typeIcon[type as keyof typeof typeIcon] ?? (
      <Activity className="h-4 w-4" />
    );

  return (
    <div className="flex items-start gap-3 py-2.5">
      <span className="mt-0.5 text-base" role="img" aria-label={type}>
        {icon}
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm text-text-primary dark:text-dark-text-primary">
          {title}
        </p>
        <p className="mt-0.5 text-xs text-text-tertiary dark:text-dark-text-tertiary">
          {time}
        </p>
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
  const priorityColor = {
    urgent: 'bg-red-500',
    high: 'bg-amber-500',
    medium: 'bg-blue-500',
    low: 'bg-gray-400',
  } as const;

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
          priorityColor[priority as keyof typeof priorityColor] ?? 'bg-gray-400',
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

  const { data: pipelines, isLoading: pipelinesLoading } = usePipelines();
  const { data: dealsData, isLoading: dealsLoading } = useDeals({ page_size: '200' });
  const { data: activitiesData, isLoading: activitiesLoading } = useActivities({
    page_size: '5',
  });
  const { data: tasksData, isLoading: tasksLoading } = useTasks({ page_size: '5' });

  const isLoading = pipelinesLoading || dealsLoading;

  const metrics = useMemo(() => {
    if (!dealsData?.results) return null;

    const deals: Deal[] = dealsData.results;
    const totalPipelineValue = deals
      .filter((d) => d.status === 'open')
      .reduce((sum, d) => sum + d.value, 0);
    const wonDeals = deals.filter((d) => d.status === 'won');
    const wonValue = wonDeals.reduce((sum, d) => sum + d.value, 0);
    const activeDeals = deals.filter((d) => d.status === 'open').length;
    const totalClosed = wonDeals.length + deals.filter((d) => d.status === 'lost').length;
    const winRate = totalClosed > 0 ? wonDeals.length / totalClosed : 0;
    const avgDealValue =
      deals.length > 0
        ? deals.reduce((sum, d) => sum + d.value, 0) / deals.length
        : 0;

    // Group deals by stage
    const stageMap = new Map<string, { count: number; value: number }>();
    for (const d of deals) {
      const name = d.stage_name || d.stage;
      const existing = stageMap.get(name) ?? { count: 0, value: 0 };
      existing.count++;
      existing.value += d.value;
      stageMap.set(name, existing);
    }

    const dealsByStage = Array.from(stageMap.entries())
      .map(([stage_name, data]) => ({ stage_name, ...data }))
      .sort((a, b) => b.value - a.value);

    return {
      total_pipeline_value: totalPipelineValue,
      won_value: wonValue,
      win_rate: winRate,
      active_deals: activeDeals,
      avg_deal_value: avgDealValue,
      deals_by_stage: dealsByStage,
      activities_this_week: activitiesData?.count ?? 0,
      tasks_due: tasksData?.count ?? 0,
    };
  }, [dealsData, activitiesData, tasksData]);

  const activities = activitiesData?.results ?? [];
  const tasks = tasksData?.results ?? [];

  const chartData = useMemo(() => {
    if (!metrics?.deals_by_stage) return [];
    return metrics.deals_by_stage.map((s) => ({
      name: s.stage_name,
      value: s.value,
      count: s.count,
    }));
  }, [metrics]);

  const hasDeals = dealsData && dealsData.results.length > 0;

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

      {/* Metric Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Total Pipeline Value"
          value={isLoading ? '' : formatCurrency(metrics?.total_pipeline_value ?? 0)}
          icon={<DollarSign className="h-5 w-5" />}
          loading={isLoading}
        />
        <MetricCard
          title="Won Deals"
          value={isLoading ? '' : formatCurrency(metrics?.won_value ?? 0)}
          icon={<Target className="h-5 w-5" />}
          loading={isLoading}
        />
        <MetricCard
          title="Win Rate"
          value={isLoading ? '' : formatPercent(metrics?.win_rate ?? 0)}
          icon={<TrendingUp className="h-5 w-5" />}
          loading={isLoading}
        />
        <MetricCard
          title="Active Deals"
          value={isLoading ? '' : String(metrics?.active_deals ?? 0)}
          icon={<Briefcase className="h-5 w-5" />}
          loading={isLoading}
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
                    fill="var(--color-brand-500, #6366f1)"
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
              <EmptyState message="No recent activity" />
            ) : (
              <div className="divide-y divide-border dark:divide-dark-border">
                {activities.map((activity) => (
                  <ActivityItem
                    key={activity.id}
                    title={activity.title}
                    type={activity.activity_type}
                    time={formatRelativeTime(activity.created_at)}
                  />
                ))}
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
      <div className="flex flex-wrap items-center gap-3">
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