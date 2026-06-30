import { type HTMLAttributes } from 'react';
import { DollarSign, Calendar, User, Building2 } from 'lucide-react';
import { cn } from '../../lib/utils';
import { Card } from './card';
import { Badge } from '../atoms/badge';
import { Skeleton } from '../atoms/skeleton';

export interface DealCardData {
  id: string;
  name: string;
  value: number;
  currency?: string;
  contact_name?: string;
  account_name?: string;
  stage_name?: string;
  expected_close_date?: string;
  win_probability?: number;
}

export interface DealCardProps extends HTMLAttributes<HTMLDivElement> {
  /** Deal data */
  deal: DealCardData;
  /** Loading state */
  loading?: boolean;
}

export function DealCard({ deal, loading = false, className, ...props }: DealCardProps) {
  if (loading) {
    return (
      <Card className={cn('w-full', className)}>
        <div className="space-y-2">
          <Skeleton variant="text" width="75%" height={16} />
          <Skeleton variant="text" width="40%" height={20} />
          <Skeleton variant="text" width="50%" height={12} />
        </div>
      </Card>
    );
  }

  return (
    <Card
      variant="interactive"
      className={cn('w-full', className)}
      {...props}
    >
      <div className="space-y-2">
        <div className="flex items-start justify-between gap-2">
          <h4 className="text-sm font-medium text-text-primary dark:text-dark-text-primary truncate">
            {deal.name}
          </h4>
          {deal.stage_name && (
            <Badge variant="info" size="sm" className="shrink-0">
              {deal.stage_name}
            </Badge>
          )}
        </div>

        <div className="flex items-center gap-1 text-base font-semibold text-text-primary dark:text-dark-text-primary">
          <DollarSign className="h-4 w-4 text-text-tertiary dark:text-dark-text-tertiary" />
          {new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: deal.currency || 'USD',
            minimumFractionDigits: 0,
          }).format(deal.value)}
        </div>

        <div className="flex flex-col gap-1">
          {deal.contact_name && (
            <div className="flex items-center gap-1.5 text-xs text-text-secondary dark:text-dark-text-secondary">
              <User className="h-3 w-3 shrink-0" />
              <span className="truncate">{deal.contact_name}</span>
            </div>
          )}
          {deal.account_name && (
            <div className="flex items-center gap-1.5 text-xs text-text-secondary dark:text-dark-text-secondary">
              <Building2 className="h-3 w-3 shrink-0" />
              <span className="truncate">{deal.account_name}</span>
            </div>
          )}
          {deal.expected_close_date && (
            <div className="flex items-center gap-1.5 text-xs text-text-tertiary dark:text-dark-text-tertiary">
              <Calendar className="h-3 w-3 shrink-0" />
              <span>{deal.expected_close_date}</span>
            </div>
          )}
        </div>

        {deal.win_probability !== undefined && (
          <div className="pt-1">
            <div className="flex items-center justify-between text-xs text-text-tertiary dark:text-dark-text-tertiary mb-1">
              <span>Win probability</span>
              <span>{deal.win_probability}%</span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-surface-tertiary dark:bg-dark-surface-tertiary overflow-hidden">
              <div
                className={cn(
                  'h-full rounded-full transition-all duration-300',
                  deal.win_probability >= 70
                    ? 'bg-emerald-500'
                    : deal.win_probability >= 40
                      ? 'bg-amber-500'
                      : 'bg-red-500',
                )}
                style={{ width: `${deal.win_probability}%` }}
              />
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}