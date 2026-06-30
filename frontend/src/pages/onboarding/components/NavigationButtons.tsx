import { Button } from '../../../components/atoms/button';

interface NavigationButtonsProps {
  currentStep: number;
  totalSteps: number;
  onBack: () => void;
  onNext: () => void;
  onSkip: () => void;
  onFinish: () => void;
  isLastStep: boolean;
  loading?: boolean;
  nextLabel?: string;
  skipLabel?: string;
}

export function NavigationButtons({
  currentStep,
  onBack,
  onNext,
  onSkip,
  onFinish,
  isLastStep,
  loading = false,
  nextLabel = 'Continue',
  skipLabel = 'Skip',
}: NavigationButtonsProps) {
  return (
    <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-200 dark:border-slate-700">
      <div>
        {currentStep > 0 && (
          <Button variant="ghost" onClick={onBack} disabled={loading}>
            ← Back
          </Button>
        )}
      </div>
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onSkip}
          className="text-sm text-gray-400 hover:text-gray-600 dark:text-slate-500 dark:hover:text-slate-300 transition-colors"
        >
          {skipLabel}
        </button>
        {isLastStep ? (
          <Button onClick={onFinish} loading={loading}>
            Go to Dashboard
          </Button>
        ) : (
          <Button onClick={onNext} loading={loading}>
            {nextLabel} →
          </Button>
        )}
      </div>
    </div>
  );
}
