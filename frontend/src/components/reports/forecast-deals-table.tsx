import type { DealForecast } from '../../types';
import { formatCurrency, formatPercent } from './shared';

interface ForecastDealsTableProps {
  deals: DealForecast[];
  loading?: boolean;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  const d = new Date(dateStr + (dateStr.length === 10 ? 'T00:00:00' : ''));
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export function ForecastDealsTable({ deals, loading }: ForecastDealsTableProps) {
  if (loading) {
    return (
      <div className="rounded-xl bg-white dark:bg-dark-surface border border-border dark:border-dark-border p-5 shadow-sm">
        <div className="h-5 w-40 bg-surface-tertiary dark:bg-dark-surface-tertiary rounded animate-pulse mb-4" />
        <div className="space-y-2 animate-pulse">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-10 bg-surface-tertiary dark:bg-dark-surface-tertiary rounded" />
          ))}
        </div>
      </div>
    );
  }

  if (!deals || deals.length === 0) {
    return null;
  }

  return (
    <div className="rounded-xl bg-white dark:bg-dark-surface border border-border dark:border-dark-border p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-text-primary dark:text-dark-text-primary mb-4">
        Deal-by-Deal Forecast
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border dark:border-dark-border">
              <th className="text-left py-2.5 px-3 font-medium text-text-secondary dark:text-dark-text-secondary text-xs uppercase tracking-wider">
                Deal
              </th>
              <th className="text-left py-2.5 px-3 font-medium text-text-secondary dark:text-dark-text-secondary text-xs uppercase tracking-wider">
                Stage
              </th>
              <th className="text-left py-2.5 px-3 font-medium text-text-secondary dark:text-dark-text-secondary text-xs uppercase tracking-wider">
                Pipeline
              </th>
              <th className="text-right py-2.5 px-3 font-medium text-text-secondary dark:text-dark-text-secondary text-xs uppercase tracking-wider">
                Value
              </th>
              <th className="text-right py-2.5 px-3 font-medium text-text-secondary dark:text-dark-text-secondary text-xs uppercase tracking-wider">
                Prob.
              </th>
              <th className="text-right py-2.5 px-3 font-medium text-text-secondary dark:text-dark-text-secondary text-xs uppercase tracking-wider">
                Weighted
              </th>
              <th className="text-right py-2.5 px-3 font-medium text-text-secondary dark:text-dark-text-secondary text-xs uppercase tracking-wider">
                Est. Close
              </th>
            </tr>
          </thead>
          <tbody>
            {deals.map((deal) => (
              <tr
                key={deal.deal_id}
                className="border-b border-border dark:border-dark-border last:border-0 hover:bg-surface-secondary dark:hover:bg-dark-surface-secondary transition-colors"
              >
                <td className="py-2.5 px-3">
                  <span className="font-medium text-text-primary dark:text-dark-text-primary">
                    {deal.deal_name}
                  </span>
                </td>
                <td className="py-2.5 px-3 text-text-secondary dark:text-dark-text-secondary">
                  {deal.stage_name}
                </td>
                <td className="py-2.5 px-3 text-text-tertiary dark:text-dark-text-tertiary">
                  {deal.pipeline_name}
                </td>
                <td className="py-2.5 px-3 text-right font-medium text-text-primary dark:text-dark-text-primary">
                  {formatCurrency(deal.deal_value)}
                </td>
                <td className="py-2.5 px-3 text-right">
                  <span className="inline-flex items-center gap-1">
                    <span
                      className={`inline-block w-1.5 h-1.5 rounded-full ${
                        deal.probability_weight >= 0.7
                          ? 'bg-emerald-500'
                          : deal.probability_weight >= 0.4
                          ? 'bg-amber-500'
                          : 'bg-slate-400'
                      }`}
                    />
                    <span className="text-text-secondary dark:text-dark-text-secondary">
                      {formatPercent(deal.probability_weight)}
                    </span>
                  </span>
                </td>
                <td className="py-2.5 px-3 text-right font-semibold text-text-primary dark:text-dark-text-primary">
                  {formatCurrency(deal.projected_value)}
                </td>
                <td className="py-2.5 px-3 text-right text-text-tertiary dark:text-dark-text-tertiary whitespace-nowrap">
                  {deal.estimated_close_date ? (
                    <span>
                      {formatDate(deal.estimated_close_date)}
                      {!deal.has_expected_date && (
                        <span className="ml-1 text-amber-500" title="Estimated from stage velocity">
                          ~
                        </span>
                      )}
                    </span>
                  ) : (
                    <span className="text-text-tertiary">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-xs text-text-tertiary dark:text-dark-text-tertiary">
        Showing {deals.length} open deal{deals.length !== 1 ? 's' : ''} sorted by estimated close date
      </p>
    </div>
  );
}