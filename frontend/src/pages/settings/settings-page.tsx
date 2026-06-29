import { useState } from 'react';
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
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { useMemberships, useInviteMember } from '../../api/teams';
import { Button } from '../../components/ui/button';
import { Card } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Modal } from '../../components/ui/modal';
import { Avatar } from '../../components/ui/avatar';
import { Skeleton } from '../../components/ui/skeleton';
import { cn } from '../../lib/utils';
import apiClient from '../../api/client';
import toast from 'react-hot-toast';
import type { Membership } from '../../types';

type SettingsTab = 'profile' | 'team' | 'integrations';

const TABS: { key: SettingsTab; label: string; icon: React.ReactNode }[] = [
  { key: 'profile', label: 'Profile', icon: <User className="h-4 w-4" /> },
  { key: 'team', label: 'Team', icon: <Users className="h-4 w-4" /> },
  { key: 'integrations', label: 'Integrations', icon: <Puzzle className="h-4 w-4" /> },
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

      <div className="pt-4 border-t border-border dark:border-dark-border">
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
  const [integrations] = useState([
    {
      key: 'google',
      name: 'Google',
      description: 'Sync emails and calendar events with Google Workspace (Gmail, Google Calendar).',
      icon: <Mail className="h-6 w-6 text-blue-600 dark:text-blue-400" />,
      connected: false,
    },
    {
      key: 'slack',
      name: 'Slack',
      description: 'Receive notifications and updates in your Slack workspace channels.',
      icon: <MessageSquare className="h-6 w-6 text-purple-600 dark:text-purple-400" />,
      connected: false,
    },
    {
      key: 'zoom',
      name: 'Zoom',
      description: 'Schedule and join Zoom meetings directly from deals and contacts.',
      icon: <Video className="h-6 w-6 text-blue-500 dark:text-blue-300" />,
      connected: false,
    },
  ]);

  const handleConnect = (name: string) => {
    toast.success(`${name} integration — coming soon`);
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

      {integrations.length === 0 ? (
        <EmptyState message="No integrations available at this time." />
      ) : (
        <div className="space-y-3">
          {integrations.map((int) => (
            <IntegrationCard
              key={int.key}
              name={int.name}
              description={int.description}
              icon={int.icon}
              connected={int.connected}
              onConnect={() => handleConnect(int.name)}
            />
          ))}
        </div>
      )}
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
        {activeTab === 'integrations' && <IntegrationsTab />}
      </Card>
    </div>
  );
}