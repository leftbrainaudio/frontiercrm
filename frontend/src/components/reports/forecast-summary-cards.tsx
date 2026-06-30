import { TrendingUp, Target, Clock } from 'lucide-react';
import { Card } from '../molecules/card';
import { formatCurrency, ReportEmptyState, ReportLoading } from './shared';
import type {
  SimpleWeightedProjection,
  WinRateAdjustedProjection,
  VelocityBasedProjection,
  WhatIfScenario,
} from '../../types';

interface ForecastSummaryCardsProps {
  simpleWeighted?: SimpleWeightedProjection;
  winRateAdjusted?: WinRateAdjustedProjection;
  velocityBased?: VelocityBasedProjection;
  whatIf?: WhatIfScenario | null;
  loading: boolean;
}

function valueWithSign(value: number): string {
  const prefix = value >= 0 ? '+' : '';
  return `${prefix}${formatCurrency(value)}`;
}

export function ForecastSummaryCards({
  simpleWeighted,
  winRateAdjusted,
  velocityBased,
  whatIf,
  loading,
}: ForecastSummaryCardsProps) {
  if (loading) {
    return <ReportLoading rows={3} />;
  }

  if (!simpleWeighted && !winRateAdjusted && !velocityBased) {
    return <ReportEmptyState message="No forecast data available for this period" />;
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {/* Simple Weighted */}
      {simpleWeighted && (
        <Card padding="md">
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-900/30 dark:text-brand-400">
                <TrendingUp className="h-4 w-4" />
              </div>
              <div>
                <p className="text-xs font-medium text-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">
                  Weighted Pipeline
                </p>
              </div>
            </div>
            <p className="text-2xl font-bold text-text-primary dark:text-dark-text-primary">
              {formatCurrency(simpleWeighted.projected_revenue)}
            </p>
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-text-tertiary dark:text-dark-text-tertiary">
              <span>{simpleWeighted.deals_in_pipeline} deals</span>
              <span>{formatCurrency(simpleWeighted.total_pipeline_value)} total</span>
            </div>
          </div>
        </Card>
      )}

      {/* Win-Rate Adjusted */}
      {winRateAdjusted && (
        <Card padding="md">
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400">
                <Target className="h-4 w-4" />
              </div>
              <div>
                <p className="text-xs font-medium text-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">
                  Win-Rate Adjusted
                </p>
              </div>
            </div>
            <p className="text-2xl font-bold text-text-primary dark:text-dark-text-primary">
              {formatCurrency(winRateAdjusted.projected_revenue)}
            </p>
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-text-tertiary dark:text-dark-text-tertiary">
              <span>Win rate: {(winRateAdjusted.historical_win_rate * 100).toFixed(0)}%</span>
              <span>Factor: {winRateAdjusted.adjustment_factor.toFixed(2)}</span>
            </div>
          </div>
        </Card>
      )}

      {/* Velocity-Based */}
      {velocityBased && (
        <Card padding="md">
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400">
                <Clock className="h-4 w-4" />
              </div>
              <div>
                <p className="text-xs font-medium text-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">
                  Velocity Forecast
                </p>
              </div>
            </div>
            <p className="text-2xl font-bold text-text-primary dark:text-dark-text-primary">
              {formatCurrency(velocityBased.projected_revenue)}
            </p>
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-text-tertiary dark:text-dark-text-tertiary">
              <span>{velocityBased.expected_close_count} expected closes</span>
              <span>{velocityBased.avg_days_to_close.toFixed(1)}d avg</span>
            </div>
          </div>
        </Card>
      )}

      {/* What-If Comparison */}
      {whatIf && (
        <Card padding="md" variant="outline">
          <div className="space-y-3">
            <p className="text-xs font-medium text-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">
              What-If: {whatIf.stage_name}
            </p>
            <div className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="text-text-secondary dark:text-dark-text-secondary">Current</span>
                <span className="font-medium">{formatCurrency(whatIf.current_projected_value)}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-text-secondary dark:text-dark-text-secondary">
                  Scenario ({(whatIf.scenario_close_rate * 100).toFixed(0)}%)
                </span>
                <span className="font-medium">{formatCurrency(whatIf.scenario_projected_value)}</span>
              </div>
              <div className="flex items-center justify-between text-sm font-bold pt-1 border-t border-border dark:border-dark-border">
                <span className={whatIf.upside >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}>
                  Upside
                </span>
                <span className={whatIf.upside >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}>
                  {valueWithSign(whatIf.upside)}
                </span>
              </div>
            </div>
            <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary">
              {whatIf.deals_affected} deal{whatIf.deals_affected !== 1 ? 's' : ''} affected in this stage
            </p>
          </div>
        </Card>
      )}
    </div>
  );
}
