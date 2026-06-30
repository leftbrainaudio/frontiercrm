import { useMemo } from 'react';
import { Card } from '../molecules/card';

interface StageOption {
  id: string;
  name: string;
}

interface ScenarioFormProps {
  stages: StageOption[];
  selectedStage: string;
  closeRate: number;
  confidenceLevel: string;
  onStageChange: (stage: string) => void;
  onCloseRateChange: (rate: number) => void;
  onConfidenceChange: (level: string) => void;
  disabled?: boolean;
}

const CONFIDENCE_OPTIONS = [
  { value: 'conservative', label: 'Conservative (×0.8)' },
  { value: 'medium', label: 'Medium (×1.0)' },
  { value: 'optimistic', label: 'Optimistic (×1.15)' },
];

export function ScenarioForm({
  stages,
  selectedStage,
  closeRate,
  confidenceLevel,
  onStageChange,
  onCloseRateChange,
  onConfidenceChange,
  disabled,
}: ScenarioFormProps) {
  const uniqueStages = useMemo(() => {
    const seen = new Set<string>();
    return stages.filter((s) => {
      if (seen.has(s.name)) return false;
      seen.add(s.name);
      return true;
    });
  }, [stages]);

  return (
    <Card title="Scenario Builder" padding="md">
      <div className="space-y-4">
        {/* Stage selector */}
        <div>
          <label
            htmlFor="scenario-stage"
            className="block text-xs font-medium text-text-secondary dark:text-dark-text-secondary uppercase tracking-wider mb-1.5"
          >
            Target Stage
          </label>
          <select
            id="scenario-stage"
            value={selectedStage}
            onChange={(e) => onStageChange(e.target.value)}
            disabled={disabled}
            className="w-full rounded-lg border border-border dark:border-dark-border bg-white dark:bg-dark-surface px-3 py-2 text-sm text-text-primary dark:text-dark-text-primary focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:opacity-50"
          >
            <option value="">-- Select a stage --</option>
            {uniqueStages.map((s) => (
              <option key={s.id} value={s.name}>
                {s.name}
              </option>
            ))}
          </select>
        </div>

        {/* Close rate slider */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label
              htmlFor="scenario-close-rate"
              className="text-xs font-medium text-text-secondary dark:text-dark-text-secondary uppercase tracking-wider"
            >
              Scenario Close Rate
            </label>
            <span className="text-sm font-medium text-text-primary dark:text-dark-text-primary">
              {(closeRate * 100).toFixed(0)}%
            </span>
          </div>
          <input
            id="scenario-close-rate"
            type="range"
            min="0"
            max="100"
            value={Math.round(closeRate * 100)}
            onChange={(e) => onCloseRateChange(parseInt(e.target.value, 10) / 100)}
            disabled={disabled}
            className="w-full h-2 rounded-full appearance-none cursor-pointer accent-brand-500 bg-surface-tertiary dark:bg-dark-surface-tertiary disabled:opacity-50"
          />
          <div className="flex justify-between text-xs text-text-tertiary dark:text-dark-text-tertiary mt-1">
            <span>0%</span>
            <span>50%</span>
            <span>100%</span>
          </div>
        </div>

        {/* Confidence level */}
        <div>
          <label
            htmlFor="scenario-confidence"
            className="block text-xs font-medium text-text-secondary dark:text-dark-text-secondary uppercase tracking-wider mb-1.5"
          >
            Confidence Level
          </label>
          <select
            id="scenario-confidence"
            value={confidenceLevel}
            onChange={(e) => onConfidenceChange(e.target.value)}
            disabled={disabled}
            className="w-full rounded-lg border border-border dark:border-dark-border bg-white dark:bg-dark-surface px-3 py-2 text-sm text-text-primary dark:text-dark-text-primary focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:opacity-50"
          >
            {CONFIDENCE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </Card>
  );
}
