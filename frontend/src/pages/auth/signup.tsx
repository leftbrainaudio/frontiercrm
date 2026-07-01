import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Button } from '../../components/atoms/button';
import { Input } from '../../components/atoms/input';

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
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    // Clear individual field error on change
    if (fieldErrors[name]) {
      setFieldErrors((prev) => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
    }
  };

  const validate = (): boolean => {
    const errs: Record<string, string> = {};
    if (!form.first_name.trim()) errs.first_name = 'First name is required';
    if (!form.last_name.trim()) errs.last_name = 'Last name is required';
    if (!form.email.trim()) {
      errs.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      errs.email = 'Enter a valid email address';
    }
    if (!form.password) {
      errs.password = 'Password is required';
    } else if (form.password.length < 8) {
      errs.password = 'Password must be at least 8 characters';
    }
    setFieldErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!validate()) return;

    if (form.password !== form.confirm_password) {
      setFieldErrors((prev) => ({ ...prev, confirm_password: 'Passwords do not match' }));
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
      <div className="bg-surface dark:bg-dark-surface rounded-2xl shadow-sm border border-border dark:border-dark-border p-8">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-600 text-white font-bold text-xl">
              F
            </div>
          </div>
          <h1 className="text-2xl font-bold text-text-primary dark:text-dark-text-primary">Create your account</h1>
          <p className="text-sm text-text-secondary dark:text-dark-text-secondary mt-1">
            Start managing relationships
          </p>
        </div>

        <form onSubmit={handleSubmit} noValidate className="space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-300">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <Input label="First name" name="first_name" value={form.first_name} onChange={handleChange} error={fieldErrors.first_name} required />
            <Input label="Last name" name="last_name" value={form.last_name} onChange={handleChange} error={fieldErrors.last_name} required />
          </div>

          <Input label="Email" type="email" name="email" value={form.email} onChange={handleChange} error={fieldErrors.email} placeholder="you@company.com" required />
          <Input label="Organization" name="organization_name" value={form.organization_name} onChange={handleChange} placeholder="Your Company Inc" />
          <Input label="Password" type="password" name="password" value={form.password} onChange={handleChange} error={fieldErrors.password} required />
          <Input label="Confirm password" type="password" name="confirm_password" value={form.confirm_password} onChange={handleChange} error={fieldErrors.confirm_password} required />

          <Button type="submit" loading={loading} fullWidth>
            Create account
          </Button>
        </form>

        <div className="mt-6 text-center">
          <span className="text-sm text-text-secondary dark:text-dark-text-secondary">
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