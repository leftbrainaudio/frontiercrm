import { useEffect, useState } from 'react';
import { Button } from '../../../../components/atoms/button';
import { NavigationButtons } from '../NavigationButtons';
import { useOnboarding } from '../../hooks/useOnboarding';
import type { OnboardingProgressPayload } from '../../../../types';

interface Props {
  onDone: (payload: OnboardingProgressPayload) => void;
  onSkip: () => void;
}

export function ConnectEmailStep({ onDone, onSkip }: Props) {
  const { status, fetchStatus } = useOnboarding();
  const [connecting, setConnecting] = useState(false);

  // Detect if email is already connected via status
  const isConnected = status?.email_done;

  const handleConnect = async () => {
    setConnecting(true);
    try {
      // Open Google OAuth from the social auth endpoint.
      // After successful auth the AppLayout guard redirects un-onboarded
      // users to /onboarding automatically — no need to modify the state param.
      const { data } = await (await import('../../../../api/client')).default.get<{
        authorization_url: string;
      }>('/auth/google/init/');
      window.location.href = data.authorization_url;
    } catch {
      setConnecting(false);
    }
  };

  // Poll status to detect when email gets connected via OAuth callback
  useEffect(() => {
    if (!connecting) return;
    const interval = setInterval(() => {
      fetchStatus();
    }, 3000);
    return () => clearInterval(interval);
  }, [connecting, fetchStatus]);

  // If email is now connected, mark step done
  useEffect(() => {
    if (isConnected) {
      onDone({ email_done: true });
    }
  }, [isConnected, onDone]);

  const handleNext = async () => {
    await onDone({ email_done: true });
  };

  return (
    <div className="text-center">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100 mb-2">
        Connect your email
      </h1>
      <p className="text-gray-500 dark:text-slate-400 mb-8">
        Sync your Gmail to send and receive emails from FrontierCRM.
      </p>
      <div className="max-w-md mx-auto space-y-4">
        <div className="p-6 rounded-xl bg-brand-50 dark:bg-brand-900/20 border border-brand-200 dark:border-brand-800">
          {isConnected ? (
            <div className="text-green-600 dark:text-green-400">
              <p className="font-semibold">✓ Gmail connected</p>
              <p className="text-sm mt-1">
                Your emails will sync automatically.
              </p>
            </div>
          ) : (
            <>
              <p className="text-sm text-gray-600 dark:text-slate-300 mb-4">
                Connect your Gmail account to sync emails, track conversations,
                and send messages directly from FrontierCRM.
              </p>
              <Button onClick={handleConnect} loading={connecting} className="w-full">
                Connect Gmail
              </Button>
            </>
          )}
        </div>
      </div>
      <NavigationButtons
        currentStep={3}
        totalSteps={6}
        onBack={() => {}}
        onNext={handleNext}
        onSkip={onSkip}
        onFinish={() => {}}
        isLastStep={false}
        skipLabel="Skip — I'll connect later"
      />
    </div>
  );
}