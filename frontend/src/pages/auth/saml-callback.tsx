import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import apiClient from '../../api/client';

export function SamlCallbackPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { setUser } = useAuth();
  const [error, setError] = useState('');
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');

  useEffect(() => {
    // Read tokens from URL hash fragment (#access=...&refresh=...)
    const hash = location.hash.replace(/^#/, '');
    const params = new URLSearchParams(hash);
    const access = params.get('access');
    const refresh = params.get('refresh');

    if (!access || !refresh) {
      setError('No authentication tokens received.');
      setStatus('error');
      return;
    }

    // Store tokens
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);

    // Fetch user profile
    apiClient
      .get('/accounts/me/')
      .then(({ data }) => {
        setUser(data);
        setStatus('success');
        navigate('/onboarding', { replace: true });
      })
      .catch(() => {
        setError('Failed to verify authentication.');
        setStatus('error');
      });
  }, [location.hash, navigate, setUser]);

  return (
    <div className="w-[400px] max-w-full">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-gray-200 dark:border-slate-700 p-8">
        <div className="text-center">
          {status === 'loading' && (
            <>
              <div className="flex justify-center mb-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-600 text-white font-bold text-xl">
                  F
                </div>
              </div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-2">Completing sign in</h1>
              <p className="text-sm text-gray-500 dark:text-slate-400">Please wait while we complete authentication...</p>
              <div className="mt-6 flex justify-center">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-brand-600 border-t-transparent" />
              </div>
            </>
          )}
          {status === 'success' && (
            <>
              <div className="flex justify-center mb-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-green-100 dark:bg-green-900/30 text-green-600 font-bold text-xl">
                  ✓
                </div>
              </div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-2">Signed in successfully</h1>
              <p className="text-sm text-gray-500 dark:text-slate-400">Redirecting to your dashboard...</p>
            </>
          )}
          {status === 'error' && (
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
          )}
        </div>
      </div>
    </div>
  );
}