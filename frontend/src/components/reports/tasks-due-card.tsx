import { Card } from '../ui/card';
import { Badge } from '../ui/badge';

export interface TasksDueCardProps {
  totalDue: number;
  overdue: number;
  dueToday: number;
  byPriority: Record<string, number>;
  loading?: boolean;
}

export function TasksDueCard({ totalDue, overdue, dueToday, byPriority, loading }: TasksDueCardProps) {
  if (loading) {
    return (
      <Card title="Tasks Summary" padding="lg">
        <div className="space-y-3 animate-pulse">
          <div className="h-8 bg-surface-tertiary dark:bg-dark-surface-tertiary rounded w-1/3" />
          <div className="h-4 bg-surface-tertiary dark:bg-dark-surface-tertiary rounded w-2/3" />
          <div className="h-4 bg-surface-tertiary dark:bg-dark-surface-tertiary rounded w-1/2" />
        </div>
      </Card>
    );
  }

  const priorityColors: Record<string, 'danger' | 'warning' | 'info' | 'neutral'> = {
    urgent: 'danger',
    high: 'warning',
    medium: 'info',
    low: 'neutral',
  };

  return (
    <Card title="Tasks Due" subtitle="Open tasks overview" padding="lg">
      <div className="space-y-4">
        {/* Totals */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-text-secondary dark:text-dark-text-secondary">Total open</span>
          <span className="text-2xl font-bold text-text-primary dark:text-dark-text-primary">{totalDue}</span>
        </div>

        {/* Overdue & Today */}
        <div className="flex gap-4">
          <div className="flex-1 rounded-lg bg-red-50 dark:bg-red-900/20 p-3 text-center">
            <p className="text-2xl font-bold text-red-600 dark:text-red-400">{overdue}</p>
            <p className="text-xs text-red-600/70 dark:text-red-400/70">Overdue</p>
          </div>
          <div className="flex-1 rounded-lg bg-amber-50 dark:bg-amber-900/20 p-3 text-center">
            <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">{dueToday}</p>
            <p className="text-xs text-amber-600/70 dark:text-amber-400/70">Due Today</p>
          </div>
        </div>

        {/* By priority */}
        <div className="space-y-2">
          {Object.entries(byPriority).map(([priority, count]) => (
            <div key={priority} className="flex items-center justify-between">
              <Badge variant={priorityColors[priority] ?? 'neutral'} size="sm">
                {priority}
              </Badge>
              <span className="text-sm font-medium text-text-primary dark:text-dark-text-primary">
                {count}
              </span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}