import { Button } from '../../../../components/atoms/button';
import type { OnboardingStatus } from '../../../../types';

interface Props {
  status: OnboardingStatus | null;
  onFinish: () => void;
  loading: boolean;
}

export function DoneStep({ status, onFinish, loading }: Props) {
  const skippedCount = status?.skipped_steps?.length ?? 0;

  return (
    <div className="text-center">
      <div className="flex justify-center mb-6">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30 animate-scale-fade">
          <svg
            className="w-10 h-10 text-green-600 dark:text-green-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={3}
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>
      </div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100 mb-2">
        You're all set!
      </h1>
      <p className="text-gray-500 dark:text-slate-400 mb-8">
        Explore FrontierCRM and start managing your pipeline.
      </p>
      <div className="max-w-md mx-auto space-y-3 text-left">
        <div className="p-4 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
          <p className="font-medium text-green-800 dark:text-green-200">
            ✅ Company configured
          </p>
        </div>
        {skippedCount === 0 && (
          <div className="p-4 rounded-xl bg-brand-50 dark:bg-brand-900/20 border border-brand-200 dark:border-brand-800">
            <p className="font-medium text-brand-800 dark:text-brand-200">
              🚀 All steps completed
            </p>
          </div>
        )}
        {skippedCount > 0 && (
          <div className="p-4 rounded-xl bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800">
            <p className="font-medium text-yellow-800 dark:text-yellow-200">
              ⏭ {skippedCount} step{skippedCount > 1 ? 's' : ''} skipped
            </p>
            <p className="text-sm text-yellow-600 dark:text-yellow-400 mt-1">
              You can revisit skipped steps from Settings anytime.
            </p>
          </div>
        )}
      </div>
      <div className="mt-8">
        <Button onClick={onFinish} loading={loading} size="lg">
          Go to Dashboard →
        </Button>
      </div>
    </div>
  );
}