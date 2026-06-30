import { useState, useCallback } from 'react';
import apiClient from '../../../api/client';
import type { OnboardingStatus, OnboardingProgressPayload } from '../../../types';

export function useOnboarding() {
  const [status, setStatus] = useState<OnboardingStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await apiClient.get<OnboardingStatus>(
        '/accounts/onboarding/status/',
      );
      setStatus(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Failed to load onboarding status');
    } finally {
      setLoading(false);
    }
  }, []);

  const updateProgress = useCallback(
    async (payload: OnboardingProgressPayload): Promise<OnboardingStatus | null> => {
      setLoading(true);
      setError(null);
      try {
        const { data } = await apiClient.patch<OnboardingStatus>(
          '/accounts/onboarding/progress/',
          payload,
        );
        setStatus(data);
        return data;
      } catch (err: any) {
        setError(err?.response?.data?.error ?? 'Failed to update onboarding');
        return null;
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  return { status, loading, error, fetchStatus, updateProgress };
}