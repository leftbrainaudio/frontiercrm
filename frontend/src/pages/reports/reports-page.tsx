import { useState, useMemo } from 'react';
import {
  DollarSign,
  Target,
  TrendingUp,
  Briefcase,
  Clock,
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
import { useDashboardReport, useStaleDeals } from '../../api/reports';
import { usePipelines } from '../../api/deals';
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
  const [preset, setPreset] = useState<PresetRange>('30d');
  const [startDate, setStartDate] = useState(daysAgo(30));
  const [endDate, setEndDate] = useState(today());
  const [pipelineId, setPipelineId] = useState<string>('');
  const [groupBy, setGroupBy] = useState<string>('');

  const { data: pipelines } = usePipelines();
  const { data: report, isLoading: reportLoading } = useDashboardReport({
    start_date: startDate,
    end_date: endDate,
    ...(pipelineId ? { pipeline_id: pipelineId } : {}),
    ...(groupBy ? { group_by: groupBy } : {}),
  });
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
        startDate={startDate}
        endDate={endDate}
        onDateChange={(s, e) => {
          setPreset('custom');
          setStartDate(s);
          setEndDate(e);
        }}
        pipelineId={pipelineId || undefined}
        pipelines={pipelineOptions}
        onPipelineChange={(id) => setPipelineId(id ?? '')}
        groupBy={groupBy || undefined}
        onGroupByChange={(g) => setGroupBy(g ?? '')}
      />

      <div className="space-y-6 p-6">
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
    </div>
  );
}