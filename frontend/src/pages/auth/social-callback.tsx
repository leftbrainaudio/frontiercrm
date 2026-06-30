import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

export function SocialCallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { socialLogin } = useAuth();
  const [error, setError] = useState('');

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const provider = state || 'google';

    if (!code) {
      setError('No authorization code received from provider.');
      return;
    }

    socialLogin(provider, code, window.location.origin + '/auth/callback')
      .then(() => {
        // After auth, let the guard redirect — AppLayout redirects un-onboarded
        // users to /onboarding; onboarded users go to dashboard.
        navigate('/onboarding', { replace: true });
      })
      .catch((err: any) => {
        setError(err.response?.data?.error || err.response?.data?.detail || 'Authentication failed. Please try again.');
      });
  }, [searchParams, socialLogin, navigate]);

  return (
    <div className="w-[400px] max-w-full">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-gray-200 dark:border-slate-700 p-8">
        <div className="text-center">
          {error ? (
            <>
              <div className="flex justify-center mb-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-red-100 dark:bg-red-900/30 text-red-600 font-bold text-xl">
                  !
                </div>
              </div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-2">Sign-in failed</h1>
              <p className="text-sm text-red-600 dark:text-red-400 mb-4">{error}</p>
              <button
                onClick={() => navigate('/login', { replace: true })}
                className="text-sm text-brand-600 dark:text-brand-400 hover:underline font-medium"
              >
                Back to login
              </button>
            </>
          ) : (
            <>
              <div className="flex justify-center mb-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-600 text-white font-bold text-xl">
                  F
                </div>
              </div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-2">Signing you in</h1>
              <p className="text-sm text-gray-500 dark:text-slate-400">
                Please wait while we complete authentication...
              </p>
              <div className="mt-6 flex justify-center">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-brand-600 border-t-transparent" />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
