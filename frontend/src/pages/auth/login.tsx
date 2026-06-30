import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Button } from '../../components/atoms/button';
import { Input } from '../../components/atoms/input';
import { TwoFactorChallenge } from './two-factor-challenge';
import apiClient from '../../api/client';
import type { SamlDomainCheckResponse } from '../../types';

function GoogleIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5 mr-3" aria-hidden="true">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
    </svg>
  );
}

function MicrosoftIcon() {
  return (
    <svg viewBox="0 0 21 21" className="h-5 w-5 mr-3" aria-hidden="true">
      <rect x="1" y="1" width="9" height="9" fill="#F25022" />
      <rect x="11" y="1" width="9" height="9" fill="#7FBA00" />
      <rect x="1" y="11" width="9" height="9" fill="#00A4EF" />
      <rect x="11" y="11" width="9" height="9" fill="#FFB900" />
    </svg>
  );
}

function initiateOAuth(provider: string) {
  // Use plain fetch to avoid any stale auth headers
  fetch(`/api/auth/social/${provider}/init/`)
    .then((res) => res.json())
    .then((data) => {
      if (data.authorization_url) {
        window.location.href = data.authorization_url;
      }
    })
    .catch(() => {
      // fallback — errors are handled by the redirect itself
    });
}

export function LoginPage() {
  const { login, isAwaiting2FA } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [ssoLoading, setSsoLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});

  // If we're awaiting 2FA, show the challenge screen
  if (isAwaiting2FA) {
    return <TwoFactorChallenge />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setFieldErrors({});

    // Validate fields before submitting
    const errors: { email?: string; password?: string } = {};
    if (!email.trim()) errors.email = 'Email is required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.email = 'Please enter a valid email address';
    if (!password) errors.password = 'Password is required';

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    setLoading(true);
    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.response?.data?.non_field_errors?.[0] || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  const handleSsoRedirect = async () => {
    if (!email.trim()) {
      setError('Please enter your email address first.');
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Please enter a valid email address.');
      return;
    }

    setSsoLoading(true);
    setError('');
    try {
      // Check if domain has SAML configured
      const { data } = await apiClient.get<SamlDomainCheckResponse>(
        `/auth/saml/domain-check/?email=${encodeURIComponent(email)}`
      );
      if (!data.has_saml) {
        setError('No SSO configured for this domain. Please sign in with email and password.');
        setSsoLoading(false);
        return;
      }
      // Initiate SAML login
      const { data: loginData } = await apiClient.post('/auth/saml/login/', { email });
      if (loginData.redirect_url) {
        window.location.href = loginData.redirect_url;
      } else {
        setError('Failed to initiate SSO login.');
      }
    } catch (err: any) {
      setError(err?.response?.data?.error || err?.response?.data?.detail || 'SSO login failed.');
    } finally {
      setSsoLoading(false);
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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100">Welcome back</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">
            Sign in to FrontierCRM
          </p>
        </div>

        {/* Social login buttons */}
        <div className="space-y-3 mb-6">
          <button
            type="button"
            onClick={() => initiateOAuth('google')}
            className="w-full flex items-center justify-center px-4 py-2.5 border border-gray-300 dark:border-slate-600 rounded-lg text-sm font-medium text-gray-700 dark:text-slate-300 bg-white dark:bg-slate-700 hover:bg-gray-50 dark:hover:bg-slate-600 transition-colors"
          >
            <GoogleIcon />
            Continue with Google
          </button>
          <button
            type="button"
            onClick={() => initiateOAuth('microsoft')}
            className="w-full flex items-center justify-center px-4 py-2.5 border border-gray-300 dark:border-slate-600 rounded-lg text-sm font-medium text-gray-700 dark:text-slate-300 bg-white dark:bg-slate-700 hover:bg-gray-50 dark:hover:bg-slate-600 transition-colors"
          >
            <MicrosoftIcon />
            Continue with Microsoft
          </button>
        </div>

        <div className="relative mb-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-200 dark:border-slate-700" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-white dark:bg-slate-800 text-gray-500 dark:text-slate-400">or sign in with email</span>
          </div>
        </div>

        <form onSubmit={handleSubmit} noValidate className="space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-300">
              {error}
            </div>
          )}

          <div>
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (fieldErrors.email) setFieldErrors((prev) => ({ ...prev, email: undefined }));
              }}
              placeholder="you@company.com"
              required
              error={fieldErrors.email}
              className={fieldErrors.email ? 'border-red-500 focus:border-red-500' : ''}
            />
          </div>

          <div>
            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                if (fieldErrors.password) setFieldErrors((prev) => ({ ...prev, password: undefined }));
              }}
              placeholder="Enter your password"
              required
              error={fieldErrors.password}
              className={fieldErrors.password ? 'border-red-500 focus:border-red-500' : ''}
            />
          </div>

          <Button type="submit" loading={loading} fullWidth>
            Sign in
          </Button>
        </form>

        {/* SSO button */}
        <div className="mt-4">
          <button
            type="button"
            onClick={handleSsoRedirect}
            disabled={ssoLoading}
            className="w-full flex items-center justify-center px-4 py-2.5 border border-gray-300 dark:border-slate-600 rounded-lg text-sm font-medium text-gray-700 dark:text-slate-300 bg-white dark:bg-slate-700 hover:bg-gray-50 dark:hover:bg-slate-600 transition-colors disabled:opacity-50"
          >
            {ssoLoading ? (
              <span className="flex items-center gap-2">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-brand-600 border-t-transparent" />
                Redirecting to SSO...
              </span>
            ) : (
              'Continue with SSO'
            )}
          </button>
        </div>

        <div className="mt-6 text-center">
          <Link
            to="/magic-link"
            className="text-sm text-brand-600 dark:text-brand-400 hover:underline"
          >
            Sign in with magic link
          </Link>
        </div>

        <div className="mt-4 text-center">
          <span className="text-sm text-gray-500 dark:text-slate-400">
            Don't have an account?{' '}
          </span>
          <Link to="/signup" className="text-sm text-brand-600 dark:text-brand-400 hover:underline font-medium">
            Sign up
          </Link>
        </div>
      </div>
    </div>
  );
}
