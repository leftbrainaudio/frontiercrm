import { useState } from 'react';
import { Users, UserPlus, Shield, Edit3, Check, X } from 'lucide-react';
import { useUsers, useRoles, useUpdateUserRole, useInviteMember } from '../../api/teams';
import { RoleGate } from '../../components/molecules/role-gate';
import { Button } from '../../components/atoms/button';
import { Input } from '../../components/atoms/input';
import { Avatar } from '../../components/atoms/avatar';
import { Skeleton } from '../../components/atoms/skeleton';
import toast from 'react-hot-toast';
import type { Membership, Role } from '../../types';

function EmptyState({ message, icon }: { message: string; icon?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      {icon && <div className="mb-4">{icon}</div>}
      <p className="text-sm text-text-secondary dark:text-dark-text-secondary">{message}</p>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <p className="text-sm text-red-500">{message}</p>
    </div>
  );
}

/* ────────── Invite Member Section ────────── */

function InviteMemberForm({ onSuccess }: { onSuccess: () => void }) {
  const [email, setEmail] = useState('');
  const [roleId, setRoleId] = useState('');
  const inviteMember = useInviteMember();
  const { data: roles } = useRoles();

  const handleSubmit = async () => {
    if (!email.trim()) return;
    try {
      await inviteMember.mutateAsync({ email, role_id: roleId || undefined });
      setEmail('');
      setRoleId('');
      onSuccess();
      toast.success('Invitation sent');
    } catch (err: any) {
      toast.error(err?.response?.data?.error || 'Failed to send invitation');
    }
  };

  return (
    <div className="flex items-end gap-3">
      <div className="flex-1">
        <Input
          label="Email Address"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="colleague@company.com"
        />
      </div>
      <div className="w-48">
        <label className="mb-1.5 block text-sm font-medium text-text-primary dark:text-dark-text-primary">
          Role
        </label>
        <select
          value={roleId}
          onChange={(e) => setRoleId(e.target.value)}
          className="w-full rounded-lg border border-border bg-white px-3 py-2.5 text-sm text-text-primary focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary"
        >
          <option value="">Default role</option>
          {(roles ?? []).map((r) => (
            <option key={r.id} value={r.id}>
              {r.name}
            </option>
          ))}
        </select>
      </div>
      <Button
        icon={<UserPlus className="h-4 w-4" />}
        onClick={handleSubmit}
        loading={inviteMember.isPending}
        disabled={!email.trim()}
      >
        Invite
      </Button>
    </div>
  );
}

/* ────────── Member Row ────────── */

function MemberRow({
  member,
  roles,
  onRoleChange,
}: {
  member: Membership;
  roles: Role[];
  onRoleChange: (memberId: string, roleId: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [selectedRole, setSelectedRole] = useState(member.role || '');

  const handleSave = () => {
    onRoleChange(member.id, selectedRole);
    setEditing(false);
  };

  const handleCancel = () => {
    setSelectedRole(member.role || '');
    setEditing(false);
  };

  return (
    <div className="flex items-center gap-4 px-4 py-3 hover:bg-surface-secondary/50 dark:hover:bg-dark-surface-secondary/50 transition-colors">
      <Avatar
        fallback={(member.user_email?.[0] || '?').toUpperCase()}
        size="md"
      />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-text-primary dark:text-dark-text-primary truncate">
          {member.user_name || member.user_email}
        </p>
        <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary">
          {member.user_email}
        </p>
      </div>
      <div className="w-48">
        {editing ? (
          <div className="flex items-center gap-1">
            <select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              className="flex-1 rounded border border-border bg-white px-2 py-1 text-xs dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary"
            >
              {roles.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
            <button onClick={handleSave} className="p-1 text-emerald-600 hover:text-emerald-700">
              <Check className="h-4 w-4" />
            </button>
            <button onClick={handleCancel} className="p-1 text-red-500 hover:text-red-600">
              <X className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <div className="flex items-center justify-between">
            <span className="text-sm text-text-secondary dark:text-dark-text-secondary">
              {member.role_name || '—'}
            </span>
            <RoleGate permission="team.manage_roles">
              <button
                onClick={() => setEditing(true)}
                className="p-1 text-text-tertiary hover:text-text-primary opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <Edit3 className="h-3.5 w-3.5" />
              </button>
            </RoleGate>
          </div>
        )}
      </div>
      <div className="w-28 text-right text-xs text-text-tertiary dark:text-dark-text-tertiary shrink-0">
        {member.joined_at
          ? new Date(member.joined_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
          : '—'}
      </div>
    </div>
  );
}

/* ────────── Role Card ────────── */

function RoleCard({ role, memberCount }: { role: Role; memberCount: number }) {
  return (
    <div className="rounded-xl border border-border dark:border-dark-border p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Shield className="h-4 w-4 text-brand-500" />
          <h4 className="text-sm font-semibold text-text-primary dark:text-dark-text-primary">
            {role.name}
          </h4>
        </div>
        {role.is_admin && (
          <span className="rounded-full bg-brand-100 px-2 py-0.5 text-[10px] font-medium text-brand-700 dark:bg-brand-900/30 dark:text-brand-300">
            Admin
          </span>
        )}
      </div>
      {role.description && (
        <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary mb-2 line-clamp-2">
          {role.description}
        </p>
      )}
      <div className="flex items-center justify-between">
        <span className="text-xs text-text-secondary dark:text-dark-text-secondary">
          {memberCount} member{memberCount !== 1 ? 's' : ''}
        </span>
        <span className="text-[10px] text-text-tertiary dark:text-dark-text-tertiary">
          {Object.keys(role.permissions || {}).length} permissions
        </span>
      </div>
    </div>
  );
}

/* ────────── Main Page ────────── */

export default function UsersPage() {
  const { data: memberships, isLoading: membersLoading, isError: membersError } = useUsers();
  const { data: roles, isLoading: rolesLoading } = useRoles();
  const [inviteKey, setInviteKey] = useState(0);

  const updateRoleMutation = useUpdateUserRole();

  const handleRoleChange = (membershipId: string, roleId: string) => {
    updateRoleMutation.mutate({ membershipId, roleId });
  };

  const members: Membership[] = memberships ?? [];
  const rolesList: Role[] = roles ?? [];

  // Count members per role
  const memberCountByRole: Record<string, number> = {};
  members.forEach((m) => {
    const roleId = m.role;
    if (roleId) {
      memberCountByRole[roleId] = (memberCountByRole[roleId] || 0) + 1;
    }
  });

  if (membersLoading || rolesLoading) {
    return (
      <div className="space-y-4 p-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} width="100%" height={48} />
        ))}
      </div>
    );
  }

  if (membersError) {
    return <ErrorState message="Failed to load team members" />;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-xl font-semibold text-text-primary dark:text-dark-text-primary">
          User Management
        </h2>
        <p className="text-sm text-text-secondary dark:text-dark-text-secondary mt-1">
          Manage team members, roles, and invitations
        </p>
      </div>

      {/* Invite Section */}
      <RoleGate permission="team.invite" fallback={null}>
        <div className="rounded-xl border border-border dark:border-dark-border p-4">
          <h3 className="text-sm font-semibold text-text-primary dark:text-dark-text-primary mb-3 flex items-center gap-2">
            <UserPlus className="h-4 w-4" />
            Invite Member
          </h3>
          <InviteMemberForm key={inviteKey} onSuccess={() => setInviteKey((k) => k + 1)} />
        </div>
      </RoleGate>

      {/* Team Members */}
      <div>
        <h3 className="text-sm font-semibold text-text-primary dark:text-dark-text-primary mb-3 flex items-center gap-2">
          <Users className="h-4 w-4" />
          Team Members ({members.length})
        </h3>
        {members.length === 0 ? (
          <EmptyState message="No team members yet. Invite someone to get started." />
        ) : (
          <div className="divide-y divide-border dark:divide-dark-border rounded-xl border border-border dark:border-dark-border">
            {members.map((member) => (
              <div key={member.id} className="group">
                <MemberRow
                  member={member}
                  roles={rolesList}
                  onRoleChange={handleRoleChange}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Role Templates */}
      <RoleGate permission="team.manage_roles" fallback={null}>
        <div>
          <h3 className="text-sm font-semibold text-text-primary dark:text-dark-text-primary mb-3 flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Role Templates
          </h3>
          {rolesList.length === 0 ? (
            <EmptyState message="No roles defined yet." />
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {rolesList.map((role) => (
                <RoleCard
                  key={role.id}
                  role={role}
                  memberCount={memberCountByRole[role.id] || 0}
                />
              ))}
            </div>
          )}
        </div>
      </RoleGate>
    </div>
  );
}