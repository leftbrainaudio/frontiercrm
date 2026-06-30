import { ONBOARDING_STEPS } from '../../../types';

interface StepIndicatorProps {
  currentStep: number;
  completedSteps: Set<string>;
  skippedSteps: string[];
  onStepClick: (index: number) => void;
}

export function StepIndicator({
  currentStep,
  completedSteps,
  skippedSteps,
  onStepClick,
}: StepIndicatorProps) {
  return (
    <div className="flex items-center justify-center gap-0">
      {ONBOARDING_STEPS.map((step, i) => {
        const isCompleted = completedSteps.has(step.key);
        const isSkipped = skippedSteps.includes(step.key);
        const isCurrent = currentStep === i;
        const isClickable = isCompleted || i < currentStep;

        return (
          <div key={step.key} className="flex items-center">
            {/* Step dot + label */}
            <div className="flex flex-col items-center">
              <button
                type="button"
                disabled={!isClickable}
                onClick={() => isClickable && onStepClick(i)}
                className={`
                  w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold transition-all
                  ${isCurrent ? 'ring-2 ring-brand-500 ring-offset-2 bg-brand-500 text-white' : ''}
                  ${isCompleted && !isCurrent ? 'bg-brand-500 text-white' : ''}
                  ${isSkipped && !isCompleted ? 'bg-gray-300 dark:bg-slate-600 text-gray-500 dark:text-slate-400 line-through' : ''}
                  ${!isCompleted && !isCurrent && !isSkipped ? 'bg-gray-200 dark:bg-slate-700 text-gray-400 dark:text-slate-500' : ''}
                  ${isClickable ? 'cursor-pointer hover:opacity-80' : 'cursor-default'}
                `}
              >
                {isCompleted ? '✓' : i + 1}
              </button>
              <span
                className={`text-xs mt-1 whitespace-nowrap ${
                  isCurrent
                    ? 'text-brand-600 dark:text-brand-400 font-medium'
                    : 'text-gray-400 dark:text-slate-500'
                }`}
              >
                {step.label}
              </span>
            </div>
            {/* Connector line */}
            {i < ONBOARDING_STEPS.length - 1 && (
              <div
                className={`w-8 sm:w-12 h-0.5 mx-1 sm:mx-2 ${
                  i < currentStep ? 'bg-brand-400' : 'bg-gray-200 dark:bg-slate-700'
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
