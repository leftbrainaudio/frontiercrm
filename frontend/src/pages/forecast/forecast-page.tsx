import { useState, useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import {
  DollarSign,
  TrendingUp,
  Target,
  ArrowRight,
  Shield,
  BarChart3,
  Clock,
} from 'lucide-react';
import { usePipelines } from '../../api/deals';
import { useForecast } from '../../api/reports';
import { formatCurrency, formatPercent, MetricCardSmall, type MetricCardData } from '../../components/reports/shared';
import { ForecastDealsTable } from '../../components/reports/forecast-deals-table';

function formatMonth(month: string): string {
  const d = new Date(month + '-01');
  return d.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
}

function formatPercent2(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

type ForecastRange = 'quarter' | 'half-year' | 'year';
type ForecastConfidence = 'conservative' | 'medium' | 'optimistic';

const RANGE_OPTIONS: { value: ForecastRange; label: string }[] = [
  { value: 'quarter', label: 'Next 3 Months' },
  { value: 'half-year', label: 'Next 6 Months' },
  { value: 'year', label: 'Next 12 Months' },
];

const CONFIDENCE_OPTIONS: { value: ForecastConfidence; label: string; shortLabel: string; color: string }[] = [
  { value: 'conservative', label: 'Conservative (×0.8)', shortLabel: 'Worst Case', color: 'bg-amber-500' },
  { value: 'medium', label: 'Medium (×1.0)', shortLabel: 'Most Likely', color: 'bg-brand-500' },
  { value: 'optimistic', label: 'Optimistic (×1.15)', shortLabel: 'Best Case', color: 'bg-emerald-500' },
];

export function ForecastPage() {
  const [pipelineId, setPipelineId] = useState<string>('');
  const [range, setRange] = useState<ForecastRange>('quarter');
  const [confidenceLevel, setConfidenceLevel] = useState<ForecastConfidence>('medium');
  const [scenarioStage, setScenarioStage] = useState<string>('');
  const [scenarioCloseRate, setScenarioCloseRate] = useState<number>(0.5);

  const { data: pipelines } = usePipelines();
  const { data: forecast, isLoading } = useForecast({
    ...(pipelineId ? { pipeline_id: pipelineId } : {}),
    range,
    confidence_level: confidenceLevel,
    ...(scenarioStage ? { scenario_stage: scenarioStage, scenario_close_rate: scenarioCloseRate } : {}),
  });

  const pipelineOptions = useMemo(() => {
    if (!pipelines) return [];
    return pipelines.map((p) => ({ id: p.id, name: p.name }));
  }, [pipelines]);

  // Build scenario options from pipeline stages
  const stageOptions = useMemo(() => {
    if (!pipelines) return [];
    const stages: { id: string; name: string }[] = [];
    const seen = new Set<string>();
    for (const p of pipelines) {
      for (const s of p.stages) {
        if (!seen.has(s.name)) {
          seen.add(s.name);
          stages.push({ id: s.id, name: s.name });
        }
      }
    }
    return stages;
  }, [pipelines]);

  // Summary card data
  const summaryCards: MetricCardData[] = useMemo(() => {
    if (!forecast) return [];
    const p = forecast.projections;
    return [
      {
        title: 'Projected Revenue',
        value: formatCurrency(p.velocity_based.projected_revenue),
        change: `Velocity: ${p.velocity_based.expected_close_count} deals expected`,
        positive: true,
        icon: <DollarSign className="h-5 w-5" />,
      },
      {
        title: 'Weighted Pipeline',
        value: formatCurrency(p.simple_weighted.projected_revenue),
        change: `${p.simple_weighted.deals_in_pipeline} deals at avg probability`,
        positive: true,
        icon: <Shield className="h-5 w-5" />,
      },
      {
        title: 'Win-Rate Adjusted',
        value: formatCurrency(p.win_rate_adjusted.projected_revenue),
        change: `Historical win rate: ${formatPercent2(p.win_rate_adjusted.historical_win_rate)}`,
        positive: true,
        icon: <Target className="h-5 w-5" />,
      },
      {
        title: 'Expected Deals Closed',
        value: `${p.velocity_based.expected_close_count}`,
        change: `${p.velocity_based.deals_with_expected_dates} deals with dates · ${p.velocity_based.avg_days_to_close.toFixed(1)}d avg`,
        positive: true,
        icon: <Clock className="h-5 w-5" />,
      },
    ];
  }, [forecast]);

  // Monthly chart data
  const chartData = useMemo(() => {
    if (!forecast?.projections?.velocity_based?.monthly_breakdown) return [];
    return forecast.projections.velocity_based.monthly_breakdown.map((item) => ({
      month: formatMonth(item.month),
      projected_value: item.projected_value,
      expected_deals: item.expected_deals,
    }));
  }, [forecast]);

  // What-if visible
  const showWhatIf = scenarioStage.length > 0;

  // Confidence badge for header
  const activeConfidence = CONFIDENCE_OPTIONS.find((c) => c.value === confidenceLevel);

  // ── Skeleton Loading State ──
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background dark:bg-dark-background">
        <div className="p-3 sm:p-6 space-y-6 animate-pulse">
          {/* Header */}
          <div className="h-8 w-56 bg-surface-tertiary dark:bg-dark-surface-tertiary rounded" />
          {/* Controls */}
          <div className="flex flex-wrap gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-10 w-40 bg-surface-tertiary dark:bg-dark-surface-tertiary rounded-lg" />
            ))}
          </div>
          {/* Summary cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-28 bg-surface-tertiary dark:bg-dark-surface-tertiary rounded-xl" />
            ))}
          </div>
          {/* Chart */}
          <div className="h-[320px] bg-surface-tertiary dark:bg-dark-surface-tertiary rounded-xl" />
          {/* Table skeleton */}
          <div className="h-48 bg-surface-tertiary dark:bg-dark-surface-tertiary rounded-xl" />
        </div>
      </div>
    );
  }

  // ── Empty State ──
  if (!forecast) {
    return (
      <div className="min-h-screen bg-background dark:bg-dark-background">
        <div className="p-3 sm:p-6">
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-surface-secondary dark:bg-dark-surface-secondary mb-4">
              <BarChart3 className="h-8 w-8 text-text-tertiary dark:text-dark-text-tertiary" />
            </div>
            <h3 className="text-base font-semibold text-text-primary dark:text-dark-text-primary mb-1">
              No Forecast Data
            </h3>
            <p className="text-sm text-text-tertiary dark:text-dark-text-tertiary max-w-sm">
              No deals match the current filter criteria. Create deals in your pipeline
              to see revenue projections and forecasts.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background dark:bg-dark-background">
      <div className="p-3 sm:p-6 space-y-6">
        {/* ── Page Header ── */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-lg font-semibold text-text-primary dark:text-dark-text-primary">
              Pipeline Forecast
            </h1>
            <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary">
              {forecast.period.label} &middot; {forecast.period.start_date} &ndash; {forecast.period.end_date}
              {activeConfidence && (
                <span className="ml-2">
                  &middot; Scenario: {activeConfidence.shortLabel}
                </span>
              )}
            </p>
          </div>
        </div>

        {/* ── Controls Row ── */}
        <div className="flex flex-wrap items-end gap-4">
          {/* Pipeline filter */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">
              Pipeline
            </label>
            <select
              value={pipelineId}
              onChange={(e) => setPipelineId(e.target.value)}
              className="rounded-lg border border-border dark:border-dark-border bg-white dark:bg-dark-surface px-3 py-1.5 text-sm text-text-primary dark:text-dark-text-primary"
            >
              <option value="">All Pipelines</option>
              {pipelineOptions.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          {/* Date Range Selector */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">
              Forecast Range
            </label>
            <div className="flex rounded-lg border border-border dark:border-dark-border overflow-hidden">
              {RANGE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setRange(opt.value)}
                  className={`px-3 py-1.5 text-sm font-medium transition-colors ${
                    range === opt.value
                      ? 'bg-brand-600 text-white'
                      : 'bg-white dark:bg-dark-surface text-text-secondary dark:text-dark-text-secondary hover:bg-surface-secondary dark:hover:bg-dark-surface-secondary'
                  } ${opt.value === 'quarter' ? '' : 'border-l border-border dark:border-dark-border'}`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Scenario Toggle */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">
              Scenario
            </label>
            <div className="flex rounded-lg border border-border dark:border-dark-border overflow-hidden">
              {CONFIDENCE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setConfidenceLevel(opt.value)}
                  className={`px-3 py-1.5 text-sm font-medium transition-colors ${
                    confidenceLevel === opt.value
                      ? 'bg-brand-600 text-white'
                      : 'bg-white dark:bg-dark-surface text-text-secondary dark:text-dark-text-secondary hover:bg-surface-secondary dark:hover:bg-dark-surface-secondary'
                  } ${opt.value === 'conservative' ? '' : 'border-l border-border dark:border-dark-border'}`}
                >
                  {opt.shortLabel}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* ── Summary Cards ── */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {summaryCards.map((card, i) => (
            <MetricCardSmall key={i} {...card} />
          ))}
        </div>

        {/* ── Revenue Projection Chart ── */}
        <div className="rounded-xl bg-white dark:bg-dark-surface border border-border dark:border-dark-border p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-text-primary dark:text-dark-text-primary">
              Revenue Projection — Monthly Breakdown
            </h3>
            <span className="text-xs text-text-tertiary dark:text-dark-text-tertiary">
              {forecast.period.label}
            </span>
          </div>
          {chartData.length === 0 ? (
            <div className="flex h-[280px] items-center justify-center text-sm text-text-tertiary dark:text-dark-text-tertiary">
              No monthly breakdown data for this period
            </div>
          ) : (
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 8, right: 8, left: -8, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border dark:stroke-dark-border" />
                  <XAxis dataKey="month" tick={{ fontSize: 11 }} className="text-text-tertiary dark:text-dark-text-tertiary" />
                  <YAxis
                    tick={{ fontSize: 11 }}
                    className="text-text-tertiary dark:text-dark-text-tertiary"
                    tickFormatter={(v: number) =>
                      v >= 1000000 ? `$${(v / 1000000).toFixed(1)}M` : v >= 1000 ? `$${(v / 1000).toFixed(0)}k` : `$${v}`
                    }
                  />
                  <Tooltip
                    contentStyle={{
                      borderRadius: '8px',
                      border: '1px solid var(--color-border)',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                      fontSize: '13px',
                    }}
                    formatter={(value: number, _name: string) => [formatCurrency(value), 'Projected']}
                    labelFormatter={(label: string) => label}
                  />
                  <Bar
                    dataKey="projected_value"
                    fill={confidenceLevel === 'optimistic' ? '#22c55e' : confidenceLevel === 'conservative' ? '#f59e0b' : '#6366f1'}
                    radius={[4, 4, 0, 0]}
                    name="Projected Revenue"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* ── What-If Scenario Controls ── */}
        <div className="rounded-xl bg-white dark:bg-dark-surface border border-border dark:border-dark-border p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-text-primary dark:text-dark-text-primary mb-4">
            What-If Scenario
          </h3>
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">
                Stage
              </label>
              <select
                value={scenarioStage}
                onChange={(e) => setScenarioStage(e.target.value)}
                className="rounded-lg border border-border dark:border-dark-border bg-white dark:bg-dark-surface px-3 py-1.5 text-sm text-text-primary dark:text-dark-text-primary min-w-[160px]"
              >
                <option value="">Select a stage...</option>
                {stageOptions.map((s) => (
                  <option key={s.id} value={s.name}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1.5 flex-1 max-w-xs">
              <label className="text-xs font-medium text-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">
                Close Rate: {formatPercent2(scenarioCloseRate)}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={scenarioCloseRate}
                onChange={(e) => setScenarioCloseRate(parseFloat(e.target.value))}
                className="w-full accent-brand-600"
              />
            </div>
          </div>

          {/* What-If Results */}
          {showWhatIf && forecast.what_if && (
            <div className="mt-4 p-4 rounded-lg bg-brand-50 dark:bg-brand-900/20 border border-brand-200 dark:border-brand-800">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-text-secondary dark:text-dark-text-secondary uppercase tracking-wider mb-1">
                    {forecast.what_if.stage_name} — Deals affected: {forecast.what_if.deals_affected}
                  </p>
                  <div className="flex items-center gap-3 text-sm">
                    <span className="text-text-secondary dark:text-dark-text-secondary">
                      Current: {formatCurrency(forecast.what_if.current_projected_value)}
                    </span>
                    <ArrowRight className="h-4 w-4 text-text-tertiary" />
                    <span className="font-semibold text-brand-700 dark:text-brand-300">
                      Scenario: {formatCurrency(forecast.what_if.scenario_projected_value)}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary">Upside</p>
                  <p className="text-lg font-bold text-emerald-600 dark:text-emerald-400">
                    +{formatCurrency(forecast.what_if.upside)}
                  </p>
                </div>
              </div>
            </div>
          )}

          {showWhatIf && !forecast.what_if && (
            <div className="mt-4 text-sm text-text-tertiary dark:text-dark-text-tertiary">
              No deals found in stage &quot;{scenarioStage}&quot; for the current period.
            </div>
          )}
        </div>

        {/* ── Deal-by-Deal Breakdown ── */}
        <ForecastDealsTable deals={forecast.deal_forecasts} />

        {/* ── Monthly Breakdown Table ── */}
        {forecast.projections.velocity_based.monthly_breakdown.length > 0 && (
          <div className="rounded-xl bg-white dark:bg-dark-surface border border-border dark:border-dark-border p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-text-primary dark:text-dark-text-primary mb-4">
              Monthly Breakdown
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border dark:border-dark-border">
                    <th className="text-left py-2 px-3 font-medium text-text-secondary dark:text-dark-text-secondary text-xs uppercase tracking-wider">Month</th>
                    <th className="text-right py-2 px-3 font-medium text-text-secondary dark:text-dark-text-secondary text-xs uppercase tracking-wider">Projected Value</th>
                    <th className="text-right py-2 px-3 font-medium text-text-secondary dark:text-dark-text-secondary text-xs uppercase tracking-wider">Expected Deals</th>
                  </tr>
                </thead>
                <tbody>
                  {forecast.projections.velocity_based.monthly_breakdown.map((item) => (
                    <tr key={item.month} className="border-b border-border dark:border-dark-border last:border-0">
                      <td className="py-2.5 px-3 text-text-primary dark:text-dark-text-primary">
                        {formatMonth(item.month)}
                      </td>
                      <td className="py-2.5 px-3 text-right font-medium text-text-primary dark:text-dark-text-primary">
                        {formatCurrency(item.projected_value)}
                      </td>
                      <td className="py-2.5 px-3 text-right text-text-secondary dark:text-dark-text-secondary">
                        {item.expected_deals}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── Export Button ── */}
        <div className="flex justify-end">
          <button
            onClick={() => {
              if (!forecast) return;
              const params = new URLSearchParams();
              if (pipelineId) params.set('pipeline_id', pipelineId);
              params.set('range', range);
              params.set('confidence_level', confidenceLevel);
              if (scenarioStage) {
                params.set('scenario_stage', scenarioStage);
                params.set('scenario_close_rate', String(scenarioCloseRate));
              }
              const url = `/api/reports/export/forecast/csv/?${params.toString()}`;
              const a = document.createElement('a');
              a.href = url;
              a.download = `forecast-${forecast.period.label.replace(/\s+/g, '-').toLowerCase()}.csv`;
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
            }}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition-colors"
          >
            Export CSV
          </button>
        </div>
      </div>
    </div>
  );
}