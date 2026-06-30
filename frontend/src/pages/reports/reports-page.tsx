import { useState, useMemo } from 'react';
import {
  DollarSign,
  Target,
  TrendingUp,
  Briefcase,
  Clock,
  Download,
  FileText,
} from 'lucide-react';
import { ReportHeader, type PresetRange } from '../../components/reports/report-header';
import { MetricCardsRow } from '../../components/reports/metric-cards-row';
import { PipelineValueChart } from '../../components/reports/pipeline-value-chart';
import { WinRateChart } from '../../components/reports/win-rate-chart';
import { ActivityMetricsChart } from '../../components/reports/activity-metrics-chart';
import { DealVelocityTable } from '../../components/reports/deal-velocity-table';
import { StageFunnel } from '../../components/reports/stage-funnel';
import { TopPerformersTable } from '../../components/reports/top-performers-table';
import { StaleDealsList } from '../../components/reports/stale-deals-list';
import { TasksDueCard } from '../../components/reports/tasks-due-card';
import { ForecastSummaryCards } from '../../components/reports/forecast-summary-cards';
import { ForecastChart } from '../../components/reports/forecast-chart';
import { ScenarioForm } from '../../components/reports/scenario-form';
import { QuarterSelector } from '../../components/reports/quarter-selector';
import { useDashboardReport, useForecast, useStaleDeals } from '../../api/reports';
import { usePipelines } from '../../api/deals';
import { ExportButton } from '../../components/ui/export-button';
import { BarChart3 } from 'lucide-react';
import {
  formatCurrency,
  formatPercent,
  formatChange,
  formatChangeAbsolute,
  isPositiveChange,
} from '../../components/reports/shared';

const PRESET_DAYS: Record<PresetRange, number> = {
  '7d': 7,
  '30d': 30,
  '90d': 90,
  'quarter': 90,
  'custom': 30,
};

function daysAgo(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().split('T')[0];
}

function today(): string {
  return new Date().toISOString().split('T')[0];
}

export function ReportsPage() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'forecast'>('dashboard');
  const [preset, setPreset] = useState<PresetRange>('30d');
  const [startDate, setStartDate] = useState(daysAgo(30));
  const [endDate, setEndDate] = useState(today());
  const [pipelineId, setPipelineId] = useState<string>('');

  // Forecast-specific state
  const [forecastQuarter, setForecastQuarter] = useState(() => {
    const now = new Date();
    const y = now.getFullYear();
    const q = Math.floor(now.getMonth() / 3) + 1;
    return `${y}-Q${q}`;
  });
  const [scenarioStage, setScenarioStage] = useState('');
  const [scenarioCloseRate, setScenarioCloseRate] = useState(0.75);
  const [forecastConfidence, setForecastConfidence] = useState('medium');
  const [groupBy, setGroupBy] = useState<string>('');

  const { data: pipelines } = usePipelines();
  const { data: report, isLoading: reportLoading } = useDashboardReport({
    ...(activeTab === 'dashboard' ? {} : { skip: 'true' }),
    start_date: startDate,
    end_date: endDate,
    ...(pipelineId ? { pipeline_id: pipelineId } : {}),
    ...(groupBy ? { group_by: groupBy } : {}),
  });

  const { data: forecastData, isLoading: forecastLoading } = useForecast(
    activeTab === 'forecast'
      ? {
          quarter: forecastQuarter,
          ...(pipelineId ? { pipeline_id: pipelineId } : {}),
          ...(scenarioStage ? { scenario_stage: scenarioStage } : {}),
          ...(scenarioStage ? { scenario_close_rate: scenarioCloseRate } : {}),
          confidence_level: forecastConfidence as 'conservative' | 'medium' | 'optimistic',
        }
      : undefined
  );

  const { data: staleDealsData, isLoading: staleLoading } = useStaleDeals({
    days_since_activity: '14',
    past_close_date: 'true',
    limit: '20',
  });

  const handlePresetChange = (newPreset: PresetRange) => {
    setPreset(newPreset);
    if (newPreset !== 'custom') {
      const days = PRESET_DAYS[newPreset];
      setStartDate(daysAgo(days));
      setEndDate(today());
    }
  };

  const pipelineOptions = useMemo(() => {
    if (!pipelines) return [];
    return pipelines.map((p) => ({ id: p.id, name: p.name }));
  }, [pipelines]);

  // Pipeline stage options for scenario form
  const stageOptions = useMemo(() => {
    if (!pipelines) return [];
    const stages: { id: string; name: string }[] = [];
    const seen = new Set<string>();
    for (const p of pipelines) {
      for (const s of p.stages) {
        if (!seen.has(s.id)) {
          seen.add(s.id);
          stages.push({ id: s.id, name: s.name });
        }
      }
    }
    return stages;
  }, [pipelines]);

  const summaryCards = useMemo(() => {
    if (!report) return [];
    const s = report.summary;
    return [
      {
        title: 'Pipeline Value',
        value: formatCurrency(s.total_pipeline_value),
        change: formatChange(s.pipeline_value_change),
        positive: isPositiveChange(s.pipeline_value_change),
        icon: <DollarSign className="h-5 w-5" />,
      },
      {
        title: 'Won Deals',
        value: formatCurrency(s.won_value),
        change: formatChange(s.won_value_change),
        positive: isPositiveChange(s.won_value_change),
        icon: <Target className="h-5 w-5" />,
      },
      {
        title: 'Win Rate',
        value: formatPercent(s.win_rate),
        change: s.win_rate_change !== null ? `${s.win_rate_change >= 0 ? '+' : ''}${s.win_rate_change.toFixed(1)}pp` : null,
        positive: isPositiveChange(s.win_rate_change),
        icon: <TrendingUp className="h-5 w-5" />,
      },
      {
        title: 'Avg Days to Close',
        value: `${s.avg_days_to_close.toFixed(1)}d`,
        change: s.avg_days_to_close > 0 ? `${s.avg_days_to_close.toFixed(1)}d avg` : null,
        positive: s.avg_days_to_close <= 45,
        icon: <Clock className="h-5 w-5" />,
      },
      {
        title: 'Active Deals',
        value: String(s.active_deals),
        change: formatChangeAbsolute(s.active_deals_change),
        positive: isPositiveChange(s.active_deals_change),
        icon: <Briefcase className="h-5 w-5" />,
      },
      {
        title: 'Weighted Pipeline',
        value: formatCurrency(s.weighted_pipeline),
        change: null,
        positive: true,
        icon: <TrendingUp className="h-5 w-5" />,
      },
    ];
  }, [report]);

  const loading = reportLoading;
  const reportData = report ?? undefined;

  const activityByType = reportData?.activity_metrics.by_type ?? [];
  const activityByDay = reportData?.activity_metrics.by_day ?? [];
  const activityTotal = reportData?.activity_metrics.total ?? 0;
  const callsDuration = reportData?.activity_metrics.calls_with_duration.avg_minutes;

  return (
    <div className="min-h-screen bg-background dark:bg-dark-background">
      <ReportHeader
        title="Reports & Analytics"
        preset={preset}
        onPresetChange={handlePresetChange}
        startDate={activeTab === 'dashboard' ? startDate : undefined}
        endDate={activeTab === 'dashboard' ? endDate : undefined}
        onDateChange={(s, e) => {
          setPreset('custom');
          setStartDate(s);
          setEndDate(e);
        }}
        pipelineId={pipelineId || undefined}
        pipelines={pipelineOptions}
        onPipelineChange={(id) => setPipelineId(id ?? '')}
        groupBy={activeTab === 'dashboard' ? (groupBy || undefined) : undefined}
        onGroupByChange={(g) => setGroupBy(g ?? '')}
      />

      {/* Export Buttons */}
      {activeTab === 'dashboard' && (
        <div className="flex items-center gap-2 px-3 sm:px-6 pt-3 pb-0">
          <ExportButton url="/reports/export/pipeline/csv/" filename="report.csv" label="Export CSV" variant="secondary" size="sm" />
          <ExportButton url="/reports/export/html/" filename="report.html" label="Printable Report" variant="ghost" size="sm" />
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-border dark:border-dark-border px-3 sm:px-6">
        <div className="flex gap-6">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'dashboard'
                ? 'border-brand-500 text-brand-600 dark:text-brand-400'
                : 'border-transparent text-text-tertiary dark:text-dark-text-tertiary hover:text-text-primary dark:hover:text-dark-text-primary'
            }`}
          >
            Dashboard
          </button>
          <button
            onClick={() => setActiveTab('forecast')}
            className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'forecast'
                ? 'border-brand-500 text-brand-600 dark:text-brand-400'
                : 'border-transparent text-text-tertiary dark:text-dark-text-tertiary hover:text-text-primary dark:hover:text-dark-text-primary'
            }`}
          >
            <span className="inline-flex items-center gap-1.5">
              <BarChart3 className="h-4 w-4" />
              Forecast
            </span>
          </button>
        </div>
      </div>

      {activeTab === 'dashboard' ? (
        /* ── Dashboard Tab ── */
        <div className="space-y-6 p-3 sm:p-6">
          {/* Section 1: Key Metric Cards */}
          <MetricCardsRow cards={summaryCards} columns={6} />

          {/* Section 2: Pipeline Value Trend */}
          <PipelineValueChart
            data={reportData?.pipeline_value_trend ?? []}
            loading={loading}
          />

          {/* Section 3: Pipeline by Stage + Conversion Funnel */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <WinRateChart
                dealsByStage={reportData?.deals_by_stage ?? []}
                loading={loading}
              />
            </div>
            <div>
              <StageFunnel
                data={reportData?.win_rate_by_stage ?? []}
                loading={loading}
              />
            </div>
          </div>

          {/* Section 4: Deal Velocity */}
          <DealVelocityTable
            data={reportData?.deal_velocity ?? []}
            loading={loading}
          />

          {/* Section 5: Activity Metrics */}
          <ActivityMetricsChart
            byType={activityByType}
            byDay={activityByDay}
            total={activityTotal}
            callsAvgDuration={callsDuration}
            loading={loading}
          />

          {/* Section 6: Tasks + Stale Deals */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div>
              <TasksDueCard
                totalDue={reportData?.tasks_summary.total_due ?? 0}
                overdue={reportData?.tasks_summary.overdue ?? 0}
                dueToday={reportData?.tasks_summary.due_today ?? 0}
                byPriority={reportData?.tasks_summary.by_priority ?? {}}
                loading={loading}
              />
            </div>
            <div className="lg:col-span-2">
              <StaleDealsList
                data={staleDealsData?.stale_deals ?? []}
                loading={staleLoading}
              />
            </div>
          </div>

          {/* Section 7: Top Performers (when group_by=owner) */}
          {reportData?.by_owner && reportData.by_owner.length > 0 && (
            <TopPerformersTable
              data={reportData.by_owner}
              loading={loading}
            />
          )}
        </div>
      ) : (
        /* ── Forecast Tab ── */
        <div className="space-y-6 p-3 sm:p-6">
          {/* Controls Row */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <QuarterSelector
              selected={forecastQuarter}
              onChange={setForecastQuarter}
            />
            <div>
              <label className="block text-xs font-medium text-text-secondary dark:text-dark-text-secondary uppercase tracking-wider mb-1.5">
                Pipeline Filter
              </label>
              <select
                value={pipelineId}
                onChange={(e) => setPipelineId(e.target.value)}
                className="w-full rounded-lg border border-border dark:border-dark-border bg-white dark:bg-dark-surface px-3 py-2 text-sm text-text-primary dark:text-dark-text-primary focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="">All Pipelines</option>
                {pipelineOptions.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
            <ScenarioForm
              stages={stageOptions}
              selectedStage={scenarioStage}
              closeRate={scenarioCloseRate}
              confidenceLevel={forecastConfidence}
              onStageChange={setScenarioStage}
              onCloseRateChange={setScenarioCloseRate}
              onConfidenceChange={setForecastConfidence}
            />
            <div>
              {/* Period info card */}
              {forecastData && (
                <div className="rounded-xl bg-white dark:bg-dark-surface border border-border dark:border-dark-border p-4 shadow-sm">
                  <p className="text-xs font-medium text-text-secondary dark:text-dark-text-secondary uppercase tracking-wider mb-1">
                    Forecast Period
                  </p>
                  <p className="text-sm font-semibold text-text-primary dark:text-dark-text-primary">
                    {forecastData.period.quarter}
                  </p>
                  <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary">
                    {forecastData.period.start_date} – {forecastData.period.end_date}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Forecast Summary Cards */}
          <ForecastSummaryCards
            simpleWeighted={forecastData?.projections.simple_weighted}
            winRateAdjusted={forecastData?.projections.win_rate_adjusted}
            velocityBased={forecastData?.projections.velocity_based}
            whatIf={forecastData?.what_if}
            loading={forecastLoading}
          />

          {/* Monthly Breakdown Chart */}
          <ForecastChart
            data={forecastData?.projections.velocity_based.monthly_breakdown}
            loading={forecastLoading}
          />

          {/* Loading state for period info */}
          {forecastLoading && !forecastData && (
            <div className="flex justify-center py-8">
              <div className="animate-spin h-6 w-6 border-2 border-brand-500 border-t-transparent rounded-full" />
            </div>
          )}

          {/* Empty state */}
          {!forecastLoading && !forecastData && (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <BarChart3 className="h-12 w-12 text-text-tertiary dark:text-dark-text-tertiary mb-3" />
              <p className="text-sm text-text-tertiary dark:text-dark-text-tertiary">
                No forecast data available. Select a quarter and configure scenarios above.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
