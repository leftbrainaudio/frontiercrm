import { NavigationButtons } from './NavigationButtons';

interface OnboardingStepProps {
  /** Step number (0-based) */
  currentStep: number;
  /** Total number of steps */
  totalSteps: number;
  /** Step title displayed at the top */
  title: string;
  /** Step subtitle/description */
  subtitle: string;
  /** Content rendered in the main area */
  children: React.ReactNode;
  /** Navigation callbacks */
  onBack?: () => void;
  onNext?: () => void;
  onSkip?: () => void;
  onFinish?: () => void;
  /** Whether this is the last step (shows "Go to Dashboard" instead of "Continue") */
  isLastStep?: boolean;
  /** Whether a loading state is active */
  loading?: boolean;
  /** Custom label for the next/finish button */
  nextLabel?: string;
  /** Custom label for the skip button */
  skipLabel?: string;
}

/**
 * Base layout component for onboarding steps.
 * Provides the title, subtitle, content area, and bottom navigation bar
 * so that individual step components can focus on their specific form content.
 */
export function OnboardingStep({
  currentStep,
  totalSteps,
  title,
  subtitle,
  children,
  onBack,
  onNext,
  onSkip,
  onFinish,
  isLastStep = false,
  loading = false,
  nextLabel,
  skipLabel,
}: OnboardingStepProps) {
  return (
    <div className="text-center">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100 mb-2">
        {title}
      </h1>
      <p className="text-gray-500 dark:text-slate-400 mb-8">{subtitle}</p>
      <div className="max-w-md mx-auto">{children}</div>
      <NavigationButtons
        currentStep={currentStep}
        totalSteps={totalSteps}
        onBack={onBack ?? (() => {})}
        onNext={onNext ?? (() => {})}
        onSkip={onSkip ?? (() => {})}
        onFinish={onFinish ?? (() => {})}
        isLastStep={isLastStep}
        loading={loading}
        nextLabel={nextLabel}
        skipLabel={skipLabel}
      />
    </div>
  );
}
