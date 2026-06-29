import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';

export function SignupPage() {
  const { signup } = useAuth();
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    username: '',
    password: '',
    confirm_password: '',
    organization_name: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (form.password !== form.confirm_password) {
      setError('Passwords do not match');
      return;
    }
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setLoading(true);
    try {
      await signup({
        email: form.email,
        username: form.username || form.email.split('@')[0],
        password: form.password,
        first_name: form.first_name,
        last_name: form.last_name,
        organization_name: form.organization_name || undefined,
      });
    } catch (err: any) {
      const data = err.response?.data;
      if (data) {
        const messages = Object.values(data).flat().join('; ');
        setError(messages || 'Signup failed');
      } else {
        setError('Signup failed. Please try again.');
      }
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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100">Create your account</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">
            Start managing relationships
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-300">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <Input label="First name" name="first_name" value={form.first_name} onChange={handleChange} required />
            <Input label="Last name" name="last_name" value={form.last_name} onChange={handleChange} required />
          </div>

          <Input label="Email" type="email" name="email" value={form.email} onChange={handleChange} placeholder="you@company.com" required />
          <Input label="Organization" name="organization_name" value={form.organization_name} onChange={handleChange} placeholder="Your Company Inc" />
          <Input label="Password" type="password" name="password" value={form.password} onChange={handleChange} required />
          <Input label="Confirm password" type="password" name="confirm_password" value={form.confirm_password} onChange={handleChange} required />

          <Button type="submit" loading={loading} fullWidth>
            Create account
          </Button>
        </form>

        <div className="mt-6 text-center">
          <span className="text-sm text-gray-500 dark:text-slate-400">
            Already have an account?{' '}
          </span>
          <Link to="/login" className="text-sm text-brand-600 dark:text-brand-400 hover:underline font-medium">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}