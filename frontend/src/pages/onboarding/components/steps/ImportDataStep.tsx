import { useNavigate } from 'react-router-dom';
import { Button } from '../../../../components/atoms/button';
import { NavigationButtons } from '../NavigationButtons';
import type { OnboardingProgressPayload } from '../../../../types';

interface Props {
  onDone: (payload: OnboardingProgressPayload) => void;
  onSkip: () => void;
}

export function ImportDataStep({ onDone, onSkip }: Props) {
  const navigate = useNavigate();

  const handleImportCsv = () => {
    onDone({ import_done: true });
    navigate('/imports');
  };

  const handleNext = async () => {
    await onDone({ import_done: true });
  };

  return (
    <div className="text-center">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100 mb-2">
        Import your data
      </h1>
      <p className="text-gray-500 dark:text-slate-400 mb-8">
        Bring in your contacts and deals from a CSV file.
      </p>
      <div className="max-w-md mx-auto space-y-4">
        <div className="p-6 rounded-xl bg-brand-50 dark:bg-brand-900/20 border border-brand-200 dark:border-brand-800">
          <p className="text-sm text-gray-600 dark:text-slate-300 mb-4">
            Upload a CSV file with your contacts and deals. We'll map the
            columns automatically and give you a preview before importing.
          </p>
          <Button onClick={handleImportCsv} className="w-full">
            Import CSV
          </Button>
        </div>
        <p className="text-xs text-gray-400 dark:text-slate-500">
          No data yet? No problem — start by adding deals manually from the
          Pipeline page after setup.
        </p>
      </div>
      <NavigationButtons
        currentStep={2}
        totalSteps={6}
        onBack={() => {}}
        onNext={handleNext}
        onSkip={onSkip}
        onFinish={() => {}}
        isLastStep={false}
        skipLabel="Skip — I'll import later"
      />
    </div>
  );
}