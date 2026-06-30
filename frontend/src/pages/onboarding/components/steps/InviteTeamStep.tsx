import { useState } from 'react';
import { Input } from '../../../../components/atoms/input';
import { Button } from '../../../../components/atoms/button';
import { NavigationButtons } from '../NavigationButtons';
import apiClient from '../../../../api/client';
import type { OnboardingProgressPayload } from '../../../../types';

interface Props {
  onDone: (payload: OnboardingProgressPayload) => void;
  onSkip: () => void;
}

export function InviteTeamStep({ onDone, onSkip }: Props) {
  const [email, setEmail] = useState('');
  const [invites, setInvites] = useState<string[]>([]);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  const addEmail = () => {
    const trimmed = email.trim();
    if (trimmed && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed) && !invites.includes(trimmed)) {
      setInvites([...invites, trimmed]);
      setEmail('');
    }
  };

  const removeEmail = (e: string) => {
    setInvites(invites.filter((i) => i !== e));
  };

  const sendInvites = async () => {
    if (invites.length === 0) return;
    setSending(true);
    try {
      await Promise.all(
        invites.map((inviteEmail) =>
          apiClient.post('/teams/memberships/invite/', {
            email: inviteEmail,
            role_id: undefined,
          }),
        ),
      );
      setSent(true);
    } catch {
      // Silently fail — still mark step as attempted
    } finally {
      setSending(false);
    }
  };

  const handleNext = async () => {
    await onDone({ invite_done: true });
  };

  return (
    <div className="text-center">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100 mb-2">
        Invite your team
      </h1>
      <p className="text-gray-500 dark:text-slate-400 mb-8">
        Add colleagues to collaborate on deals and contacts.
      </p>
      <div className="max-w-md mx-auto space-y-4 text-left">
        {/* Email input */}
        {!sent && (
          <div className="flex gap-2">
            <div className="flex-1">
              <Input
                placeholder="colleague@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyDown={(e: React.KeyboardEvent) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addEmail();
                  }
                }}
              />
            </div>
            <Button variant="outline" onClick={addEmail} className="mt-0.5">
              Add
            </Button>
          </div>
        )}

        {/* Email chips */}
        {invites.length > 0 && !sent && (
          <div className="flex flex-wrap gap-2">
            {invites.map((e) => (
              <span
                key={e}
                className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-brand-50 dark:bg-brand-900/30 text-brand-700 dark:text-brand-300 text-sm"
              >
                {e}
                <button
                  type="button"
                  onClick={() => removeEmail(e)}
                  className="hover:text-red-500"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}

        {/* Send invites button */}
        {invites.length > 0 && !sent && (
          <Button onClick={sendInvites} loading={sending} className="w-full">
            Send Invites
          </Button>
        )}

        {sent && (
          <p className="text-sm text-green-600 dark:text-green-400 text-center">
            ✓ Invitations sent!
          </p>
        )}
      </div>
      <NavigationButtons
        currentStep={1}
        totalSteps={6}
        onBack={() => {}}
        onNext={handleNext}
        onSkip={onSkip}
        onFinish={() => {}}
        isLastStep={false}
      />
    </div>
  );
}