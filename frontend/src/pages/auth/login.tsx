import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';

export function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.response?.data?.non_field_errors?.[0] || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md">
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

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-300">
              {error}
            </div>
          )}

          <Input
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
            required
          />

          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
            required
          />

          <Button type="submit" loading={loading} fullWidth>
            Sign in
          </Button>
        </form>

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