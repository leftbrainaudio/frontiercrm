import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';

export function MagicLinkPage() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch('/api/auth/magic-link/request/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) {
        const data = await res.json();
        setError(data.email?.[0] || data.detail || 'Request failed');
      } else {
        setSent(true);
      }
    } catch {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
    return (
      <div className="w-full max-w-md">
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-gray-200 dark:border-slate-700 p-8 text-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100 mb-2">Check your email</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400 mb-6">
            We sent a magic link to <strong>{email}</strong>. Click the link to sign in.
          </p>
          <Link to="/login" className="text-sm text-brand-600 dark:text-brand-400 hover:underline">
            Back to sign in
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-gray-200 dark:border-slate-700 p-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100">Magic link</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">
            We'll email you a sign-in link
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-300">
              {error}
            </div>
          )}
          <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" required />
          <Button type="submit" loading={loading} fullWidth>
            Send magic link
          </Button>
        </form>

        <div className="mt-6 text-center">
          <Link to="/login" className="text-sm text-brand-600 dark:text-brand-400 hover:underline">
            Back to sign in
          </Link>
        </div>
      </div>
    </div>
  );
}