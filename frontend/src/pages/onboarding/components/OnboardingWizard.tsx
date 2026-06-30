import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../../hooks/useAuth';
import { StepIndicator } from './StepIndicator';
import { NavigationButtons } from './NavigationButtons';
import { CompanySetupStep } from './steps/CompanySetupStep';
import { InviteTeamStep } from './steps/InviteTeamStep';
import { ImportDataStep } from './steps/ImportDataStep';
import { ConnectEmailStep } from './steps/ConnectEmailStep';
import { PipelineSetupStep } from './steps/PipelineSetupStep';
import { DoneStep } from './steps/DoneStep';
import { useOnboarding } from '../hooks/useOnboarding';
import type { OnboardingStatus, OnboardingProgressPayload } from '../../../types';
import { ONBOARDING_STEPS } from '../../../types';
import { Spinner } from '../../../components/ui/spinner';

const STEP_KEYS = ONBOARDING_STEPS.map((s) => s.key);

export function OnboardingWizard() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user, setUser } = useAuth();
  const { status, loading, fetchStatus, updateProgress } = useOnboarding();

  const [currentStep, setCurrentStep] = useState(0);
  const [localStatus, setLocalStatus] = useState<OnboardingStatus | null>(null);

  const effectiveStatus = localStatus || status;
  const isReview = searchParams.get('mode') === 'review';

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // Set initial step from saved progress
  useEffect(() => {
    if (!effectiveStatus) return;
    const firstIncomplete = STEP_KEYS.findIndex(
      (key) => !effectiveStatus[`${key}_done` as keyof OnboardingStatus],
    );
    if (firstIncomplete >= 0) {
      setCurrentStep(firstIncomplete);
    }
  }, [effectiveStatus]);

  // Handle OAuth redirect back with ?onboarding=true
  useEffect(() => {
    if (searchParams.get('onboarding') === 'true') {
      // Detect email connection by re-fetching status
      fetchStatus();
    }
  }, [searchParams, fetchStatus]);

  const handleNext = useCallback(async () => {
    if (currentStep < STEP_KEYS.length - 1) {
      setCurrentStep((s) => s + 1);
    }
  }, [currentStep]);

  const handleBack = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep((s) => s - 1);
    }
  }, [currentStep]);

  const handleSkip = useCallback(
    async (stepKey: string) => {
      await updateProgress({ skip_step: stepKey });
      setLocalStatus((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          [`${stepKey}_done` as keyof OnboardingStatus]: true,
          skipped_steps: [...prev.skipped_steps, stepKey],
        };
      });
      if (currentStep < STEP_KEYS.length - 1) {
        setCurrentStep((s) => s + 1);
      }
    },
    [currentStep, updateProgress],
  );

  const handleFinish = useCallback(async () => {
    await updateProgress({ mark_complete: true });
    setLocalStatus((prev) => {
      if (!prev) return prev;
      return { ...prev, is_onboarded: true };
    });
    if (user) setUser({ ...user, is_onboarded: true });
    navigate('/dashboard');
  }, [updateProgress, user, setUser, navigate]);

  const handleStepDone = useCallback(
    async (payload: OnboardingProgressPayload) => {
      const updated = await updateProgress(payload);
      if (updated) {
        setLocalStatus(prev => ({ ...prev!, ...updated }));
      }
    },
    [updateProgress],
  );

  if (loading && !effectiveStatus) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Spinner fullPage />
      </div>
    );
  }

  const isLastStep = currentStep >= STEP_KEYS.length - 1;

  return (
    <div className="flex-1 flex flex-col">
      {/* Top bar */}
      <div className="flex items-center justify-between px-4 sm:px-8 py-4 border-b border-gray-200 dark:border-slate-700">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white font-bold text-sm">
            F
          </div>
          <span className="font-semibold text-gray-700 dark:text-slate-300 hidden sm:inline">
            FrontierCRM
          </span>
        </div>
        <StepIndicator
          currentStep={currentStep}
          completedSteps={
            new Set(
              STEP_KEYS.filter(
                (k) => effectiveStatus?.[`${k}_done` as keyof OnboardingStatus],
              ),
            )
          }
          skippedSteps={effectiveStatus?.skipped_steps ?? []}
          onStepClick={(i) => setCurrentStep(i)}
        />
        <button
          type="button"
          onClick={() => navigate('/dashboard')}
          className="text-sm text-gray-400 hover:text-gray-600 dark:text-slate-500 dark:hover:text-slate-300"
        >
          Exit
        </button>
      </div>

      {/* Content area */}
      <div className="flex-1 flex items-center justify-center p-4 sm:p-8">
        <div className="w-full max-w-2xl">
          {/* Step content */}
          {currentStep === 0 && (
            <CompanySetupStep
              tenantName={effectiveStatus?.tenant?.name ?? ''}
              tenantIndustry={effectiveStatus?.tenant?.industry ?? ''}
              tenantLogoUrl={effectiveStatus?.tenant?.logo_url ?? ''}
              onDone={(payload) => handleStepDone(payload)}
              onSkip={() => handleSkip('company')}
            />
          )}
          {currentStep === 1 && (
            <InviteTeamStep
              onDone={(payload) => handleStepDone(payload)}
              onSkip={() => handleSkip('invite')}
            />
          )}
          {currentStep === 2 && (
            <ImportDataStep
              onDone={(payload) => handleStepDone(payload)}
              onSkip={() => handleSkip('import')}
            />
          )}
          {currentStep === 3 && (
            <ConnectEmailStep
              onDone={(payload) => handleStepDone(payload)}
              onSkip={() => handleSkip('email')}
            />
          )}
          {currentStep === 4 && (
            <PipelineSetupStep
              onDone={(payload) => handleStepDone(payload)}
              onSkip={() => handleSkip('pipeline')}
            />
          )}
          {currentStep === 5 && (
            <DoneStep
              status={effectiveStatus}
              onFinish={handleFinish}
              loading={loading}
            />
          )}
        </div>
      </div>
    </div>
  );
}