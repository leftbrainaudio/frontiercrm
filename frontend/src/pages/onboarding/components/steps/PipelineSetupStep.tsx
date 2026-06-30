import { useState } from 'react';
import { NavigationButtons } from '../NavigationButtons';
import type { OnboardingProgressPayload, PipelineTemplate } from '../../../../types';
import { PIPELINE_TEMPLATES } from '../../../../types';

interface Props {
  onDone: (payload: OnboardingProgressPayload) => void;
  onSkip: () => void;
}

const TEMPLATE_KEYS: PipelineTemplate[] = ['sales', 'saas', 'recruiting', 'custom'];

export function PipelineSetupStep({ onDone, onSkip }: Props) {
  const [selected, setSelected] = useState<PipelineTemplate | null>(null);
  const [loading, setLoading] = useState(false);

  const handleNext = async () => {
    setLoading(true);
    const payload: OnboardingProgressPayload = { pipeline_done: true };
    if (selected && selected !== 'custom') {
      payload.pipeline_template = selected;
    }
    await onDone(payload);
    setLoading(false);
  };

  return (
    <div className="text-center">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100 mb-2">
        Set up your pipeline
      </h1>
      <p className="text-gray-500 dark:text-slate-400 mb-8">
        Choose a pipeline that matches your sales process.
      </p>
      <div className="max-w-lg mx-auto space-y-3">
        {TEMPLATE_KEYS.map((key) => {
          const tpl = PIPELINE_TEMPLATES[key];
          const isSelected = selected === key;
          return (
            <button
              type="button"
              key={key}
              onClick={() => setSelected(key)}
              className={`w-full text-left p-4 rounded-xl border-2 transition-all ${
                isSelected
                  ? 'border-brand-500 bg-brand-50 dark:bg-brand-900/20'
                  : 'border-gray-200 dark:border-slate-700 hover:border-gray-300 dark:hover:border-slate-600'
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-slate-100">
                    {tpl.name}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">
                    {tpl.stages.length} stages: {tpl.stages.join(' → ')}
                  </p>
                </div>
                <div
                  className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                    isSelected
                      ? 'border-brand-500 bg-brand-500'
                      : 'border-gray-300 dark:border-slate-600'
                  }`}
                >
                  {isSelected && (
                    <div className="w-2 h-2 rounded-full bg-white" />
                  )}
                </div>
              </div>
            </button>
          );
        })}
      </div>
      <NavigationButtons
        currentStep={4}
        totalSteps={6}
        onBack={() => {}}
        onNext={handleNext}
        onSkip={onSkip}
        onFinish={() => {}}
        isLastStep={false}
        loading={loading}
      />
    </div>
  );
}