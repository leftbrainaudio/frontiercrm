import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  User,
  Users,
  Puzzle,
  AlertCircle,
  Mail,
  MessageSquare,
  Video,
  Plus,
  Check,
  LogIn,
  Rocket,
  ArrowRight,
  Table,
  Key,
  Shield,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { useMemberships, useInviteMember } from '../../api/teams';
import { Button } from '../../components/atoms/button';
import { Card } from '../../components/molecules/card';
import { Input } from '../../components/atoms/input';
import { Modal } from '../../components/molecules/modal';
import { Avatar } from '../../components/atoms/avatar';
import { Skeleton } from '../../components/atoms/skeleton';
import { cn } from '../../lib/utils';
import apiClient from '../../api/client';
import toast from 'react-hot-toast';
import type { Membership } from '../../types';
import {
  useCalendarAuthUrl,
  useCalendarCallback,
  useCalendarAuthStatus,
  useCalendarWatchStatus,
  useUpgradeCalendarScope,
  useGmailAuthUrl,
  useGmailCallback,
  useSyncConnections,
} from '../../api/sync';
import { useSlackWebhooks } from '../../api/slack';
import CustomFieldsSettingsPage from './custom-fields-page';
import { ApiKeysTab } from './api-keys-page';
import { SecurityPage } from './security-page';

type SettingsTab = 'profile' | 'team' | 'integrations' | 'security' | 'custom-fields' | 'api-keys';

const TABS: { key: SettingsTab; label: string; icon: React.ReactNode }[] = [
  { key: 'profile', label: 'Profile', icon: <User className="h-4 w-4" /> },
  { key: 'team', label: 'Team', icon: <Users className="h-4 w-4" /> },
  { key: 'security', label: 'Security', icon: <Shield className="h-4 w-4" /> },
  { key: 'integrations', label: 'Integrations', icon: <Puzzle className="h-4 w-4" /> },
  { key: 'custom-fields', label: 'Custom Fields', icon: <Table className="h-4 w-4" /> },
  { key: 'api-keys', label: 'API Keys', icon: <Key className="h-4 w-4" /> },
];

function TabSkeleton() {
  return (
    <div className="space-y-4 p-6">
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} width="100%" height={48} />
      ))}
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <h3 className="text-lg font-semibold text-text-primary dark:text-dark-text-primary">
        {message}
      </h3>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-50 dark:bg-red-900/20">
        <AlertCircle className="h-6 w-6 text-red-500 dark:text-red-400" />
      </div>
      <p className="text-sm text-text-secondary dark:text-dark-text-secondary">{message}</p>
    </div>
  );
}

/* ────────── Profile Tab ────────── */

function ProfileTab() {
  const { user, setUser } = useAuth();
  const [saving, setSaving] = useState(false);

  const [firstName, setFirstName] = useState(user?.first_name || '');
  const [lastName, setLastName] = useState(user?.last_name || '');
  const [phone, setPhone] = useState(user?.phone || '');
  const [timezone, setTimezone] = useState(user?.timezone || '');

  if (!user) return <TabSkeleton />;

  const handleSave = async () => {
    setSaving(true);
    try {
      const { data } = await apiClient.patch('/accounts/me/', {
        first_name: firstName,
        last_name: lastName,
        phone,
        timezone,
      });
      setUser(data);
      toast.success('Profile updated');
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Avatar section */}
      <div className="flex items-center gap-4">
        <Avatar
          src={user.avatar_url || undefined}
          fallback={`${user.first_name} ${user.last_name}`}
          size="xl"
        />
        <div>
          <p className="text-sm font-medium text-text-primary dark:text-dark-text-primary">
            {user.first_name} {user.last_name}
          </p>
          <p className="text-xs text-text-secondary dark:text-dark-text-secondary">{user.email}</p>
          <Button size="sm" variant="outline" className="mt-2">
            Change Avatar
          </Button>
        </div>
      </div>

      {/* Profile form */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Input
          label="First Name"
          value={firstName}
          onChange={(e) => setFirstName(e.target.value)}
        />
        <Input
          label="Last Name"
          value={lastName}
          onChange={(e) => setLastName(e.target.value)}
        />
        <Input
          label="Email"
          value={user.email}
          readOnly
          helperText="Email cannot be changed"
          className="opacity-60 cursor-not-allowed bg-gray-100"
        />
        <Input
          label="Phone"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          placeholder="+1 (555) 000-0000"
        />
        <div className="sm:col-span-2">
          <Input
            label="Timezone"
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
            placeholder="America/New_York"
          />
        </div>
      </div>

      <div className="sticky bottom-0 bg-surface pt-4 pb-2 border-t border-border dark:border-dark-border dark:bg-dark-surface">
        <Button onClick={handleSave} loading={saving}>
          Save Changes
        </Button>
      </div>
    </div>
  );
}

/* ────────── Team Tab ────────── */

function TeamTab() {
  const { data: memberships, isLoading, isError, error } = useMemberships();
  const inviteMember = useInviteMember();

  const [inviteOpen, setInviteOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('');

  const members: Membership[] = memberships ?? [];

  const handleInvite = async () => {
    if (!inviteEmail.trim()) return;
    try {
      await inviteMember.mutateAsync({
        email: inviteEmail,
        role_id: inviteRole || undefined,
      });
      setInviteEmail('');
      setInviteRole('');
      setInviteOpen(false);
      toast.success('Invitation sent');
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to send invitation');
    }
  };

  if (isLoading) return <TabSkeleton />;
  if (isError) return <ErrorState message={(error as any)?.message || 'Failed to load team members'} />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-text-primary dark:text-dark-text-primary">
            Team Members
          </h3>
          <p className="text-sm text-text-secondary dark:text-dark-text-secondary">
            {members.length} member{members.length !== 1 ? 's' : ''}
          </p>
        </div>
        <Button icon={<Plus className="h-4 w-4" />} onClick={() => setInviteOpen(true)}>
          Invite Member
        </Button>
      </div>

      {members.length === 0 ? (
        <EmptyState message="No team members yet. Invite someone to get started." />
      ) : (
        <div className="divide-y divide-border dark:divide-dark-border rounded-xl border border-border dark:border-dark-border">
          {members.map((member) => (
            <div key={member.id} className="flex items-center gap-4 px-4 py-3">
              <Avatar
                fallback={(member.user_email?.[0] || '?').toUpperCase()}
                size="md"
              />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-text-primary dark:text-dark-text-primary truncate">
                  {member.user_email}
                </p>
                <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary">
                  {member.role_name}
                </p>
              </div>
              <div className="text-xs text-text-tertiary dark:text-dark-text-tertiary shrink-0">
                Joined {member.joined_at ? new Date(member.joined_at).toLocaleDateString() : '—'}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Invite Modal */}
      <Modal
        open={inviteOpen}
        onClose={() => setInviteOpen(false)}
        title="Invite Team Member"
        size="sm"
        footer={
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setInviteOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleInvite}
              loading={inviteMember.isPending}
              disabled={!inviteEmail.trim()}
            >
              Send Invitation
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <Input
            label="Email Address"
            type="email"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            placeholder="colleague@company.com"
            required
          />
          <div>
            <label
              htmlFor="invite-role"
              className="mb-1.5 block text-sm font-medium text-text-primary dark:text-dark-text-primary"
            >
              Role
            </label>
            <select
              id="invite-role"
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
              className="w-full rounded-lg border border-border bg-white px-3 py-2.5 text-sm text-text-primary focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary"
            >
              <option value="">Default role</option>
              <option value="admin">Admin</option>
              <option value="member">Member</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>
        </div>
      </Modal>
    </div>
  );
}

/* ────────── Integrations Tab ────────── */

interface IntegrationCardProps {
  name: string;
  description: string;
  icon: React.ReactNode;
  connected: boolean;
  onConnect: () => void;
}

function IntegrationCard({ name, description, icon, connected, onConnect }: IntegrationCardProps) {
  return (
    <Card variant="interactive" padding="md" className="flex items-start gap-4">
      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-surface-secondary dark:bg-dark-surface-secondary">
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <h4 className="text-sm font-semibold text-text-primary dark:text-dark-text-primary">{name}</h4>
        <p className="mt-1 text-sm text-text-secondary dark:text-dark-text-secondary">{description}</p>
      </div>
      <div className="shrink-0">
        {connected ? (
          <div className="flex items-center gap-1.5 text-xs font-medium text-emerald-600 dark:text-emerald-400">
            <Check className="h-4 w-4" />
            Connected
          </div>
        ) : (
          <Button size="sm" variant="outline" icon={<LogIn className="h-4 w-4" />} onClick={onConnect}>
            Connect
          </Button>
        )}
      </div>
    </Card>
  );
}

function IntegrationsTab() {
  const navigate = useNavigate();
  const { data: authStatus } = useCalendarAuthStatus();
  const { data: watchStatus } = useCalendarWatchStatus();
  const calendarAuthUrl = useCalendarAuthUrl();
  const calendarCallback = useCalendarCallback();
  const upgradeScope = useUpgradeCalendarScope();
  const gmailAuthUrl = useGmailAuthUrl();
  const gmailCallback = useGmailCallback();
  const { data: connections } = useSyncConnections();
  const { data: slackWebhooks } = useSlackWebhooks();

  // Check if user has a gmail connection
  const gmailConn = connections?.find((c) => c.provider === 'gmail' && c.is_active);
  const gmailConnected = !!gmailConn && gmailConn.status === 'active';

  const handleCalendarConnect = async () => {
    try {
      const { url, state } = await calendarAuthUrl.mutateAsync();
      // Open Google OAuth popup
      const popup = window.open(url, 'google-calendar-oauth', 'width=600,height=700');
      if (!popup) {
        toast.error('Popup blocked. Please allow popups for this site.');
        return;
      }
      // Poll for the callback — the redirect URI hits the backend directly,
      // so we monitor for the popup to close, then check auth status
      const timer = setInterval(() => {
        if (popup.closed) {
          clearInterval(timer);
          calendarCallback.mutate(
            { code: '', state },
            {
              onSuccess: () => toast.success('Google Calendar connected!'),
              onError: (err: any) => {
                // The callback may fail if the popup redirects to the backend
                // and the user manually closes it. Check auth status instead.
                // This is a simplified OAuth flow — in production, use
                // a proper redirect-to-frontend pattern.
                toast.error(err?.response?.data?.error || 'Calendar OAuth failed');
              },
            },
          );
        }
      }, 1000);
    } catch {
      toast.error('Failed to generate Calendar OAuth URL');
    }
  };

  const handleGmailConnect = async () => {
    try {
      const { url, state } = await gmailAuthUrl.mutateAsync();
      const popup = window.open(url, 'gmail-oauth', 'width=600,height=700');
      if (!popup) {
        toast.error('Popup blocked. Please allow popups for this site.');
        return;
      }
      const timer = setInterval(() => {
        if (popup.closed) {
          clearInterval(timer);
          gmailCallback.mutate(
            { code: '', state },
            {
              onSuccess: () => toast.success('Gmail connected!'),
              onError: () => toast.error('Gmail OAuth failed'),
            },
          );
        }
      }, 1000);
    } catch {
      toast.error('Failed to generate Gmail OAuth URL');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-text-primary dark:text-dark-text-primary">
          Integrations
        </h3>
        <p className="text-sm text-text-secondary dark:text-dark-text-secondary">
          Connect your tools to unlock more features in FrontierCRM.
        </p>
      </div>

      <div className="space-y-3">
        {/* Gmail Card */}
        <IntegrationCard
          name="Gmail"
          description="Sync emails and contacts with your Gmail account."
          icon={<Mail className="h-6 w-6 text-blue-600 dark:text-blue-400" />}
          connected={gmailConnected}
          onConnect={handleGmailConnect}
        />

        {/* Google Calendar Card */}
        <IntegrationCard
          name="Google Calendar"
          description="Sync meetings and events from Google Calendar into your activity timeline."
          icon={<svg className="h-6 w-6 text-blue-500 dark:text-blue-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>}
          connected={authStatus?.connected ?? false}
          onConnect={handleCalendarConnect}
        />

        {authStatus?.connected && (
          <div className="rounded-xl border border-border dark:border-dark-border p-4 space-y-3">
            <h4 className="text-sm font-semibold text-text-primary dark:text-dark-text-primary">
              Calendar Sync Status
            </h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="text-text-secondary dark:text-dark-text-secondary">Account</div>
              <div className="text-text-primary dark:text-dark-text-primary">{authStatus.email}</div>

              <div className="text-text-secondary dark:text-dark-text-secondary">State</div>
              <div className="text-text-primary dark:text-dark-text-primary capitalize">{authStatus.sync_state}</div>

              <div className="text-text-secondary dark:text-dark-text-secondary">Events synced</div>
              <div className="text-text-primary dark:text-dark-text-primary">{authStatus.events_count}</div>

              <div className="text-text-secondary dark:text-dark-text-secondary">Last sync</div>
              <div className="text-text-primary dark:text-dark-text-primary">
                {authStatus.last_sync_at
                  ? new Date(authStatus.last_sync_at).toLocaleString()
                  : '—'}
              </div>
            </div>

            {/* Push notification status */}
            {watchStatus && (
              <div className="border-t border-border dark:border-dark-border pt-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-text-secondary dark:text-dark-text-secondary">
                    Push Notifications
                  </span>
                  <span
                    className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      watchStatus.push_enabled
                        ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400'
                        : 'bg-gray-50 text-gray-500 dark:bg-gray-900/20 dark:text-gray-400'
                    }`}
                  >
                    <span
                      className={`h-1.5 w-1.5 rounded-full ${
                        watchStatus.push_enabled ? 'bg-emerald-500' : 'bg-gray-400'
                      }`}
                    />
                    {watchStatus.push_enabled ? 'Active' : 'Inactive (polling)'}
                  </span>
                </div>
                {watchStatus.watch_expires_at && (
                  <p className="mt-1 text-xs text-text-tertiary dark:text-dark-text-tertiary">
                    Channel expires: {new Date(watchStatus.watch_expires_at).toLocaleDateString()} (renews automatically)
                  </p>
                )}
                {watchStatus.last_push_received_at && (
                  <p className="mt-1 text-xs text-text-tertiary dark:text-dark-text-tertiary">
                    Last notification: {new Date(watchStatus.last_push_received_at).toLocaleString()}
                  </p>
                )}
                {watchStatus.fallback_polling_active && (
                  <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">
                    Fallback polling active — push channel unavailable
                  </p>
                )}
              </div>
            )}

            {/* Scope upgrade banner */}
            {!watchStatus?.push_enabled && connections?.find(c => c.provider === 'google_calendar') && (
              <div className="border-t border-border dark:border-dark-border pt-3">
                <div className="flex items-start gap-3 rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20 px-3 py-2.5">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-amber-500 dark:text-amber-400" />
                  <div className="flex-1">
                    <p className="text-xs font-medium text-amber-800 dark:text-amber-200">
                      Write access may be needed
                    </p>
                    <p className="mt-0.5 text-xs text-amber-700 dark:text-amber-300">
                      To create events from the CRM, reconnect Google Calendar with write access.
                    </p>
                    <Button
                      size="sm"
                      variant="outline"
                      className="mt-2"
                      icon={<LogIn className="h-3.5 w-3.5" />}
                      onClick={handleCalendarConnect}
                      loading={calendarAuthUrl.isPending}
                    >
                      Reconnect with Write Access
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        <IntegrationCard
          name="Slack"
          description="Receive notifications and updates in your Slack workspace channels."
          icon={<MessageSquare className="h-6 w-6 text-purple-600 dark:text-purple-400" />}
          connected={(slackWebhooks ?? []).length > 0}
          onConnect={() => navigate('/settings/integrations/slack')}
        />

        <IntegrationCard
          name="Zoom"
          description="Schedule and join Zoom meetings directly from deals and contacts."
          icon={<Video className="h-6 w-6 text-blue-500 dark:text-blue-300" />}
          connected={false}
          onConnect={() => toast.success('Zoom integration — coming soon')}
        />
      </div>
    </div>
  );
}

/* ────────── Getting Started Section ────────── */

function GettingStartedSection() {
  const navigate = useNavigate();
  const { user } = useAuth();

  if (!user) return null;

  const label = user.is_onboarded ? 'Review Setup' : 'Continue Setup';
  const target = user.is_onboarded ? '/onboarding?mode=review' : '/onboarding';

  return (
    <div className="mb-6 rounded-xl border border-brand-200 bg-brand-50 p-4 dark:border-brand-800 dark:bg-brand-900/10">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-100 dark:bg-brand-900/30">
            <Rocket className="h-5 w-5 text-brand-600 dark:text-brand-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-brand-800 dark:text-brand-200">
              Getting Started
            </h3>
            <p className="text-xs text-brand-600 dark:text-brand-400">
              {user.is_onboarded
                ? 'Review your CRM setup or update any step.'
                : 'Complete your initial CRM setup to get the most out of FrontierCRM.'}
            </p>
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="shrink-0 border-brand-300 text-brand-700 hover:bg-brand-100 dark:border-brand-700 dark:text-brand-300 dark:hover:bg-brand-900/20"
          onClick={() => navigate(target)}
        >
          {label}
          <ArrowRight className="ml-1.5 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

/* ────────── Settings Page ────────── */

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile');

  return (
    <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6 lg:px-8">
      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-text-primary dark:text-dark-text-primary">
          Settings
        </h1>
        <p className="mt-1 text-sm text-text-secondary dark:text-dark-text-secondary">
          Manage your account, team, and integrations.
        </p>
      </div>

      {/* Getting Started section */}
      <GettingStartedSection />

      {/* Tab navigation */}
      <div className="mb-6 flex gap-1 rounded-xl bg-surface-secondary p-1 dark:bg-dark-surface-secondary">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActiveTab(tab.key)}
            className={cn(
              'flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
              activeTab === tab.key
                ? 'bg-white text-text-primary shadow-sm dark:bg-dark-surface dark:text-dark-text-primary'
                : 'text-text-secondary hover:text-text-primary dark:text-dark-text-secondary dark:hover:text-dark-text-primary',
            )}
            aria-current={activeTab === tab.key ? 'page' : undefined}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <Card padding="lg">
        {activeTab === 'profile' && <ProfileTab />}
        {activeTab === 'team' && <TeamTab />}
        {activeTab === 'security' && <SecurityPage />}
        {activeTab === 'integrations' && <IntegrationsTab />}
        {activeTab === 'custom-fields' && <CustomFieldsSettingsPage />}
        {activeTab === 'api-keys' && <ApiKeysTab />}
      </Card>
    </div>
  );
}