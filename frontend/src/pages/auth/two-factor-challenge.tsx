import React, { useState, useRef } from 'react';
import { useAuth } from '../../hooks/useAuth';

export function TwoFactorChallenge() {
  const { verifyTwoFactor, cancelTwoFactor } = useAuth();
  const [mode, setMode] = useState<'totp' | 'recovery'>('totp');
  const [code, setCode] = useState('');
  const [recoveryCode, setRecoveryCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (mode === 'totp') {
        if (code.length !== 6 || !/^\d{6}$/.test(code)) {
          setError('Please enter a 6-digit code.');
          setLoading(false);
          return;
        }
        await verifyTwoFactor(code);
      } else {
        if (!recoveryCode.trim()) {
          setError('Please enter a recovery code.');
          setLoading(false);
          return;
        }
        await verifyTwoFactor(recoveryCode.trim(), true);
      }
    } catch (err: any) {
      setError(
        err.response?.data?.code?.[0] ||
          err.response?.data?.detail ||
          err.response?.data?.code ||
          'Invalid code. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-[400px] max-w-full">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-gray-200 dark:border-slate-700 p-8">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-600 text-white font-bold text-xl">
              F
            </div>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100">Two-factor authentication</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">
            {mode === 'totp'
              ? 'Enter the code from your authenticator app'
              : 'Enter one of your recovery codes'}
          </p>
        </div>

        <form onSubmit={handleSubmit} noValidate className="space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-300">
              {error}
            </div>
          )}

          {mode === 'totp' ? (
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-slate-300">
                Authentication Code
              </label>
              <input
                ref={inputRef}
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                maxLength={6}
                value={code}
                onChange={(e) => {
                  const val = e.target.value.replace(/\D/g, '');
                  setCode(val);
                  if (error) setError('');
                }}
                placeholder="000000"
                className="w-full text-center text-2xl tracking-[0.5em] rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-4 py-3 text-gray-900 dark:text-slate-100 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                required
              />
            </div>
          ) : (
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-slate-300">
                Recovery Code
              </label>
              <input
                type="text"
                value={recoveryCode}
                onChange={(e) => {
                  setRecoveryCode(e.target.value);
                  if (error) setError('');
                }}
                placeholder="XXXXXXXX-XXXXXXXX"
                className="w-full rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-4 py-3 text-gray-900 dark:text-slate-100 text-center font-mono focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                required
              />
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center px-4 py-2.5 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-sm font-semibold transition-colors disabled:opacity-50"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Verifying...
              </span>
            ) : (
              'Verify'
            )}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            type="button"
            onClick={() => {
              setMode(mode === 'totp' ? 'recovery' : 'totp');
              setError('');
              setCode('');
              setRecoveryCode('');
            }}
            className="text-sm text-brand-600 dark:text-brand-400 hover:underline"
          >
            {mode === 'totp' ? 'Use a recovery code instead' : 'Use authenticator app instead'}
          </button>
        </div>

        <div className="mt-4 text-center">
          <button
            type="button"
            onClick={cancelTwoFactor}
            className="text-sm text-gray-500 dark:text-slate-400 hover:underline"
          >
            Cancel and return to login
          </button>
        </div>
      </div>
    </div>
  );
}
