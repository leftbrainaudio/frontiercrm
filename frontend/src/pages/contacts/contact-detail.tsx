import { useState, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  ChevronRight,
  ArrowLeft,
  Mail,
  Phone,
  MapPin,
  Building2,
  Tag,
  User,
  Globe,
  Edit,
  Trash2,
  Calendar,
  MessageSquare,
  PhoneCall,
  FileText,
  Activity as ActivityIconLucide,
  AlertCircle,
  RefreshCw,
  Briefcase,
  Check,
  X,
  Save,
} from 'lucide-react';
import { Card } from '../../components/molecules/card';
import { Avatar } from '../../components/atoms/avatar';
import { Badge } from '../../components/atoms/badge';
import { Button } from '../../components/atoms/button';
import { Skeleton } from '../../components/atoms/skeleton';
import { Input } from '../../components/atoms/input';
import { cn } from '../../lib/utils';
import { useContact, useUpdateContact, useDeleteContact } from '../../api/contacts';
import { useCustomFieldDefs } from '../../api/custom-fields';
import { useDeals } from '../../api/deals';
import { useActivities } from '../../api/activities';
import { useEmails } from '../../api/emails';
import type { Activity, Deal, EmailMessage } from '../../types';

// ── Tab Configuration ──

type TabId = 'overview' | 'activity' | 'deals' | 'notes' | 'emails';

interface Tab {
  id: TabId;
  label: string;
  icon: React.ReactNode;
}

const TABS: Tab[] = [
  { id: 'overview', label: 'Overview', icon: <User className="h-4 w-4" /> },
  { id: 'activity', label: 'Activity', icon: <ActivityIconLucide className="h-4 w-4" /> },
  { id: 'deals', label: 'Deals', icon: <Briefcase className="h-4 w-4" /> },
  { id: 'notes', label: 'Notes', icon: <FileText className="h-4 w-4" /> },
  { id: 'emails', label: 'Emails', icon: <Mail className="h-4 w-4" /> },
];

// ── Helper Components ──

function DetailRow({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-3 py-3">
      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-surface-secondary text-text-tertiary dark:bg-dark-surface-secondary dark:text-dark-text-tertiary">
        {icon}
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium text-text-tertiary dark:text-dark-text-tertiary">
          {label}
        </p>
        <div className="mt-0.5 text-sm text-text-primary dark:text-dark-text-primary">
          {value ?? <span className="italic text-text-tertiary dark:text-dark-text-tertiary">Not set</span>}
        </div>
      </div>
    </div>
  );
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDate(dateStr);
}

function ActivityIcon({ type }: { type: string }) {
  const iconMap: Record<string, React.ReactNode> = {
    task: <ActivityIconLucide className="h-4 w-4" />,
    call: <PhoneCall className="h-4 w-4" />,
    email: <Mail className="h-4 w-4" />,
    meeting: <Calendar className="h-4 w-4" />,
    note: <FileText className="h-4 w-4" />,
    deal_stage_change: <Briefcase className="h-4 w-4" />,
    deal_status_change: <Briefcase className="h-4 w-4" />,
    file_upload: <FileText className="h-4 w-4" />,
    system: <ActivityIconLucide className="h-4 w-4" />,
  };

  const colorMap: Record<string, string> = {
    note: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400',
    call: 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400',
    email: 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400',
    meeting: 'bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400',
    task: 'bg-rose-100 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400',
    deal_stage_change: 'bg-indigo-100 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-400',
    default: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  };

  return (
    <div
      className={cn(
        'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
        colorMap[type] ?? colorMap.default,
      )}
    >
      {iconMap[type] ?? <ActivityIconLucide className="h-4 w-4" />}
    </div>
  );
}

function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-50 dark:bg-red-900/20">
        <AlertCircle className="h-8 w-8 text-red-500" />
      </div>
      <h3 className="text-lg font-semibold text-text-primary dark:text-dark-text-primary">
        {message}
      </h3>
      <p className="mt-1 text-sm text-text-tertiary dark:text-dark-text-tertiary">
        Please try again or contact support.
      </p>
      {onRetry && (
        <Button
          className="mt-4"
          variant="secondary"
          icon={<RefreshCw className="h-4 w-4" />}
          onClick={onRetry}
        >
          Try Again
        </Button>
      )}
    </div>
  );
}

// ── Skeleton Loader ──

function DetailSkeleton() {
  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2">
        <Skeleton variant="text" width={80} />
        <ChevronRight className="h-4 w-4 text-text-tertiary" />
        <Skeleton variant="text" width={120} />
      </div>

      {/* Header */}
      <Card>
        <div className="flex flex-col items-center gap-4 sm:flex-row">
          <Skeleton variant="circular" width={72} height={72} />
          <div className="flex-1 space-y-2 text-center sm:text-left">
            <Skeleton variant="text" width={200} height={24} />
            <Skeleton variant="text" width={140} />
          </div>
          <div className="flex gap-2">
            <Skeleton variant="rectangular" width={90} height={36} />
            <Skeleton variant="rectangular" width={90} height={36} />
          </div>
        </div>
      </Card>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-border pb-px dark:border-dark-border">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} variant="rectangular" width={100} height={36} />
        ))}
      </div>

      {/* Content Skeleton */}
      <Card>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="flex items-start gap-3">
              <Skeleton variant="rectangular" width={32} height={32} />
              <div className="flex-1 space-y-1">
                <Skeleton variant="text" width={60} />
                <Skeleton variant="text" width={160} />
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

/* ── Custom Fields Section ── */

function CustomFieldsSection({
  customFields,
}: {
  customFields: Record<string, unknown>;
}) {
  const { data: defs } = useCustomFieldDefs('contacts');

  if (!defs || defs.length === 0) return null;

  const activeDefs = defs.filter((d) => d.is_active);

  // Only show fields that have actual values
  const entries = activeDefs
    .map((def) => ({
      def,
      value: customFields[def.id],
    }))
    .filter((e) => e.value !== undefined && e.value !== null && e.value !== '');

  if (entries.length === 0) return null;

  return (
    <Card title="Custom Fields">
      <div className="space-y-1">
        {entries.map(({ def, value }) => (
          <DetailRow
            key={def.id}
            icon={<Tag className="h-4 w-4" />}
            label={def.name}
            value={String(value)}
          />
        ))}
      </div>
    </Card>
  );
}

/* ── Tab Content Components ── */

function OverviewTab({
  contact,
  isEditing,
  formData,
  onFieldChange,
}: {
  contact: NonNullable<ReturnType<typeof useContact>['data']>;
  isEditing: boolean;
  formData: Record<string, string>;
  onFieldChange: (field: string, value: string) => void;
}) {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      <Card title="Contact Information" className="md:col-span-2">
        <div className="grid grid-cols-1 gap-x-8 gap-y-1 sm:grid-cols-2">
          {isEditing ? (
            <>
              <div className="py-2">
                <Input
                  label="Email"
                  value={formData.email}
                  onChange={(e) => onFieldChange('email', e.target.value)}
                  size="sm"
                />
              </div>
              <div className="py-2">
                <Input
                  label="Phone"
                  value={formData.phone}
                  onChange={(e) => onFieldChange('phone', e.target.value)}
                  size="sm"
                />
              </div>
              <div className="py-2">
                <Input
                  label="Mobile"
                  value={formData.mobile}
                  onChange={(e) => onFieldChange('mobile', e.target.value)}
                  size="sm"
                />
              </div>
              <div className="py-2">
                <Input
                  label="Job Title"
                  value={formData.job_title}
                  onChange={(e) => onFieldChange('job_title', e.target.value)}
                  size="sm"
                />
              </div>
              <div className="py-2">
                <Input
                  label="Department"
                  value={formData.department}
                  onChange={(e) => onFieldChange('department', e.target.value)}
                  size="sm"
                />
              </div>
              <div className="py-2">
                <Input label="Account" value={contact.account_name || ''} size="sm" readOnly />
              </div>
              <div className="py-2">
                <Input
                  label="Street"
                  value={formData.street}
                  onChange={(e) => onFieldChange('street', e.target.value)}
                  size="sm"
                />
              </div>
              <div className="py-2">
                <Input
                  label="City"
                  value={formData.city}
                  onChange={(e) => onFieldChange('city', e.target.value)}
                  size="sm"
                />
              </div>
              <div className="py-2">
                <Input
                  label="State"
                  value={formData.state}
                  onChange={(e) => onFieldChange('state', e.target.value)}
                  size="sm"
                />
              </div>
              <div className="py-2">
                <Input
                  label="Country"
                  value={formData.country}
                  onChange={(e) => onFieldChange('country', e.target.value)}
                  size="sm"
                />
              </div>
            </>
          ) : (
            <>
              <DetailRow
                icon={<Mail className="h-4 w-4" />}
                label="Email"
                value={
                  <a
                    href={`mailto:${contact.email}`}
                    className="text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300"
                  >
                    {contact.email}
                  </a>
                }
              />
              <DetailRow
                icon={<Phone className="h-4 w-4" />}
                label="Phone"
                value={contact.phone || contact.mobile || 'Not set'}
              />
              <DetailRow
                icon={<MapPin className="h-4 w-4" />}
                label="Address"
                value={
                  [contact.street, contact.city, contact.state, contact.country]
                    .filter(Boolean)
                    .join(', ') || 'Not set'
                }
              />
              <DetailRow
                icon={<Building2 className="h-4 w-4" />}
                label="Account"
                value={
                  contact.account_name ? (
                    <Badge variant="neutral" size="sm">
                      {contact.account_name}
                    </Badge>
                  ) : (
                    'Not set'
                  )
                }
              />
              <DetailRow
                icon={<Tag className="h-4 w-4" />}
                label="Tags"
                value={
                  contact.tags.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {contact.tags.map((tag) => (
                        <Badge key={tag} variant="default" size="sm">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  ) : (
                    'None'
                  )
                }
              />
              <DetailRow
                icon={<User className="h-4 w-4" />}
                label="Owner"
                value={contact.owner_id || 'Unassigned'}
              />
              <DetailRow
                icon={<Globe className="h-4 w-4" />}
                label="Source"
                value={contact.source || 'Unknown'}
              />
              <DetailRow
                icon={<Calendar className="h-4 w-4" />}
                label="Created"
                value={formatDate(contact.created_at)}
              />
            </>
          )}
        </div>
      </Card>

      <Card title="Job Details">
        <div className="space-y-1">
          <DetailRow
            icon={<Briefcase className="h-4 w-4" />}
            label="Job Title"
            value={contact.job_title || 'Not set'}
          />
          <DetailRow
            icon={<Building2 className="h-4 w-4" />}
            label="Department"
            value={contact.department || 'Not set'}
          />
        </div>
      </Card>

      <Card title="Social & Web">
        <div className="space-y-1">
          <DetailRow
            icon={<Globe className="h-4 w-4" />}
            label="LinkedIn"
            value={
              contact.linkedin_url ? (
                <a
                  href={contact.linkedin_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300"
                >
                  View Profile
                </a>
              ) : (
                'Not set'
              )
            }
          />
          <DetailRow
            icon={<MessageSquare className="h-4 w-4" />}
            label="Twitter"
            value={contact.twitter_handle ? `@${contact.twitter_handle}` : 'Not set'}
          />
        </div>
      </Card>

      <CustomFieldsSection customFields={contact.custom_fields} />
    </div>
  );
}

function ActivityTab({ contactId }: { contactId: string }) {
  const navigate = useNavigate();
  const { data, isLoading, isError, refetch } = useActivities({
    entity_type: 'contacts',
    entity_id: contactId,
    page_size: '50',
  });

  if (isLoading) {
    return (
      <Card>
        <div className="space-y-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex items-start gap-3">
              <Skeleton variant="circular" width={32} height={32} />
              <div className="flex-1 space-y-1.5">
                <Skeleton variant="text" width="60%" />
                <Skeleton variant="text" width="30%" />
              </div>
            </div>
          ))}
        </div>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card>
        <ErrorState message="Failed to load activities" onRetry={() => refetch()} />
      </Card>
    );
  }

  const activities = data?.results ?? [];

  if (activities.length === 0) {
    return (
      <Card>
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-surface-secondary dark:bg-dark-surface-secondary">
            <ActivityIconLucide className="h-6 w-6 text-text-tertiary dark:text-dark-text-tertiary" />
          </div>
          <p className="text-sm text-text-tertiary dark:text-dark-text-tertiary">
            No activity recorded for this contact yet.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-4 top-2 bottom-2 w-px bg-border dark:bg-dark-border" />

        <div className="space-y-0">
          {activities.map((activity) => (
            <div key={activity.id} className="relative flex items-start gap-4 py-3 pl-0">
              <ActivityIcon type={activity.activity_type} />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-text-primary dark:text-dark-text-primary">
                  {activity.title}
                </p>
                {activity.description && (
                  <p className="mt-0.5 text-sm text-text-secondary dark:text-dark-text-secondary line-clamp-2">
                    {activity.description}
                  </p>
                )}
                <p className="mt-1 text-xs text-text-tertiary dark:text-dark-text-tertiary">
                  {formatRelativeTime(activity.created_at)}
                  {activity.duration_minutes && ` · ${activity.duration_minutes} min`}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
      {activities.length > 0 && (
        <div className="border-t border-border dark:border-dark-border pt-3 text-center">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(`/timeline?actor_id=${contactId}`)}
          >
            View full timeline →
          </Button>
        </div>
      )}
    </Card>
  );
}

function DealsTab({ contactId }: { contactId: string }) {
  const { data, isLoading, isError, refetch } = useDeals({
    contact: contactId,
    page_size: '50',
  });

  if (isLoading) {
    return (
      <Card>
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex items-center justify-between">
              <div className="space-y-1">
                <Skeleton variant="text" width={180} />
                <Skeleton variant="text" width={100} />
              </div>
              <Skeleton variant="text" width={80} />
            </div>
          ))}
        </div>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card>
        <ErrorState message="Failed to load deals" onRetry={() => refetch()} />
      </Card>
    );
  }

  const deals = data?.results ?? [];

  if (deals.length === 0) {
    return (
      <Card>
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-surface-secondary dark:bg-dark-surface-secondary">
            <Briefcase className="h-6 w-6 text-text-tertiary dark:text-dark-text-tertiary" />
          </div>
          <p className="text-sm text-text-tertiary dark:text-dark-text-tertiary">
            No deals associated with this contact.
          </p>
        </div>
      </Card>
    );
  }

  const statusColor: Record<string, 'default' | 'success' | 'warning' | 'danger'> = {
    open: 'warning',
    won: 'success',
    lost: 'danger',
    abandoned: 'neutral',
  };

  return (
    <Card className="overflow-hidden p-0">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-border bg-surface-secondary dark:border-dark-border dark:bg-dark-surface-secondary">
            <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-text-secondary">
              Deal Name
            </th>
            <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-text-secondary">
              Stage
            </th>
            <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-text-secondary">
              Value
            </th>
            <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-text-secondary">
              Status
            </th>
            <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-text-secondary">
              Close Date
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border dark:divide-dark-border">
          {deals.map((deal) => (
            <tr
              key={deal.id}
              className="transition-colors hover:bg-surface-tertiary dark:hover:bg-dark-surface-tertiary"
            >
              <td className="px-4 py-3 font-medium text-text-primary dark:text-dark-text-primary">
                {deal.name}
              </td>
              <td className="px-4 py-3 text-text-secondary dark:text-dark-text-secondary">
                {deal.stage_name}
              </td>
              <td className="px-4 py-3 text-text-secondary dark:text-dark-text-secondary">
                {new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: deal.currency,
                  minimumFractionDigits: 0,
                }).format(deal.value)}
              </td>
              <td className="px-4 py-3">
                <Badge variant={statusColor[deal.status] ?? 'neutral'} size="sm">
                  {deal.status}
                </Badge>
              </td>
              <td className="px-4 py-3 text-text-tertiary dark:text-dark-text-tertiary">
                {deal.expected_close_date
                  ? formatDate(deal.expected_close_date)
                  : '-'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

function NotesTab({ contactId }: { contactId: string }) {
  const { data, isLoading, isError, refetch } = useActivities({
    entity_type: 'contacts',
    entity_id: contactId,
    activity_type: 'note',
    page_size: '50',
  });

  if (isLoading) {
    return (
      <Card>
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="space-y-2">
              <Skeleton variant="rectangular" height={80} />
            </div>
          ))}
        </div>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card>
        <ErrorState message="Failed to load notes" onRetry={() => refetch()} />
      </Card>
    );
  }

  const notes = data?.results ?? [];

  if (notes.length === 0) {
    return (
      <Card>
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-surface-secondary dark:bg-dark-surface-secondary">
            <FileText className="h-6 w-6 text-text-tertiary dark:text-dark-text-tertiary" />
          </div>
          <p className="text-sm text-text-tertiary dark:text-dark-text-tertiary">
            No notes for this contact yet.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {notes.map((note) => (
        <Card key={note.id} variant="outline">
          <div className="flex items-start justify-between">
            <p className="text-sm text-text-primary dark:text-dark-text-primary whitespace-pre-wrap">
              {note.description || note.title}
            </p>
          </div>
          <p className="mt-2 text-xs text-text-tertiary dark:text-dark-text-tertiary">
            {formatRelativeTime(note.created_at)}
          </p>
        </Card>
      ))}
    </div>
  );
}

// ── Email Tab ──

function EmailsTab({ contactId, contactEmail }: { contactId: string; contactEmail: string }) {
  const { data, isLoading, isError, refetch } = useEmails({
    entity_type: 'contacts',
    entity_id: contactId,
    page_size: '30',
  });

  if (isLoading) {
    return (
      <Card>
        <div className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-start gap-3">
              <Skeleton variant="circular" width={32} height={32} />
              <div className="flex-1 space-y-1.5">
                <Skeleton variant="text" width="60%" />
                <Skeleton variant="text" width="40%" />
                <Skeleton variant="text" width="20%" />
              </div>
            </div>
          ))}
        </div>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card>
        <ErrorState message="Failed to load emails" onRetry={() => refetch()} />
      </Card>
    );
  }

  const emails = data?.results ?? [];

  if (emails.length === 0) {
    return (
      <Card>
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-surface-secondary dark:bg-dark-surface-secondary">
            <Mail className="h-6 w-6 text-text-tertiary dark:text-dark-text-tertiary" />
          </div>
          <p className="text-sm text-text-tertiary dark:text-dark-text-tertiary">
            No emails found for this contact.
          </p>
          {contactEmail && (
            <a
              href={`mailto:${contactEmail}`}
              className="mt-2 text-sm text-brand-600 hover:text-brand-700 dark:text-brand-400"
            >
              Send an email to {contactEmail}
            </a>
          )}
        </div>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden p-0">
      <div className="divide-y divide-border dark:divide-dark-border">
        {emails.map((email) => (
          <div
            key={email.id}
            className="flex items-start gap-3 px-4 py-3 transition-colors hover:bg-surface-tertiary dark:hover:bg-dark-surface-tertiary"
          >
            <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400">
              <Mail className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between gap-2">
                <p className="truncate text-sm font-medium text-text-primary dark:text-dark-text-primary">
                  {email.subject || '(No subject)'}
                </p>
                <Badge
                  variant={email.direction === 'inbound' ? 'default' : 'neutral'}
                  size="sm"
                >
                  {email.direction === 'inbound' ? 'Received' : 'Sent'}
                </Badge>
              </div>
              {email.body_text && (
                <p className="mt-0.5 line-clamp-2 text-sm text-text-secondary dark:text-dark-text-secondary">
                  {email.body_text}
                </p>
              )}
              <p className="mt-1 text-xs text-text-tertiary dark:text-dark-text-tertiary">
                {email.direction === 'inbound'
                  ? `From: ${email.from_email}`
                  : `To: ${email.to_emails?.join(', ')}`}
                {' · '}
                {formatRelativeTime(email.sent_at || email.created_at)}
              </p>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

// ── Main Component ──

export function ContactDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [isEditing, setIsEditing] = useState(false);

  // Form state for editing
  const [formData, setFormData] = useState<Record<string, string>>({});

  const updateContact = useUpdateContact();
  const deleteContact = useDeleteContact();

  const {
    data: contact,
    isLoading,
    isError,
    refetch,
  } = useContact(id);

  // Initialize form data when contact loads or edit mode opens
  const startEditing = useCallback(() => {
    if (!contact) return;
    setFormData({
      first_name: contact.first_name || '',
      last_name: contact.last_name || '',
      email: contact.email || '',
      phone: contact.phone || '',
      mobile: contact.mobile || '',
      job_title: contact.job_title || '',
      department: contact.department || '',
      street: contact.street || '',
      city: contact.city || '',
      state: contact.state || '',
      country: contact.country || '',
      linkedin_url: contact.linkedin_url || '',
      twitter_handle: contact.twitter_handle || '',
    });
    setIsEditing(true);
  }, [contact]);

  const cancelEditing = useCallback(() => {
    setIsEditing(false);
    setFormData({});
  }, []);

  const handleFieldChange = useCallback(
    (field: string, value: string) => {
      setFormData((prev) => ({ ...prev, [field]: value }));
    },
    [],
  );

  const saveContact = useCallback(async () => {
    if (!id) return;
    try {
      await updateContact.mutateAsync({ id, ...formData });
      toast.success('Contact updated successfully');
      setIsEditing(false);
      setFormData({});
      refetch();
    } catch (err) {
      toast.error('Failed to update contact');
    }
  }, [id, formData, updateContact, refetch]);

  if (isLoading) {
    return <DetailSkeleton />;
  }

  if (isError || !contact) {
    return (
      <div className="space-y-6">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm text-text-secondary dark:text-dark-text-secondary">
          <Link
            to="/contacts"
            className="hover:text-text-primary dark:hover:text-dark-text-primary transition-colors"
          >
            Contacts
          </Link>
          <ChevronRight className="h-4 w-4" />
          <span className="text-text-tertiary dark:text-dark-text-tertiary">Not found</span>
        </nav>

        <Card>
          <ErrorState
            message="Contact not found"
            onRetry={() => refetch()}
          />
        </Card>
      </div>
    );
  }

  const handleDelete = async () => {
    if (!window.confirm(`Are you sure you want to delete ${contact.full_name}?`)) return;
    if (!id) return;
    try {
      await deleteContact.mutateAsync(id);
      toast.success('Contact deleted successfully');
      navigate('/contacts');
    } catch {
      toast.error('Failed to delete contact');
    }
  };

  return (
    <div className="space-y-6">
      {/* Back button + Breadcrumb */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="sm"
          icon={<ArrowLeft className="h-4 w-4" />}
          onClick={() => navigate('/contacts')}
          aria-label="Back to contacts"
        />
        <nav className="flex items-center gap-2 text-sm text-text-secondary dark:text-dark-text-secondary">
          <Link
            to="/contacts"
            className="hover:text-text-primary dark:hover:text-dark-text-primary transition-colors"
          >
            Contacts
          </Link>
          <ChevronRight className="h-4 w-4" />
          <span className="text-text-primary dark:text-dark-text-primary font-medium truncate max-w-[200px]">
            {contact.full_name}
          </span>
        </nav>
      </div>

      {/* Contact Header */}
      <Card>
        <div className="flex flex-col items-center gap-4 sm:flex-row">
          <Avatar
            src={contact.avatar_url || undefined}
            fallback={`${contact.first_name} ${contact.last_name}`}
            size="xl"
          />
          <div className="flex-1 text-center sm:text-left">
            {isEditing ? (
              <div className="flex flex-wrap gap-3">
                <div className="w-40">
                  <Input
                    label="First Name"
                    value={formData.first_name}
                    onChange={(e) => handleFieldChange('first_name', e.target.value)}
                    size="sm"
                  />
                </div>
                <div className="w-40">
                  <Input
                    label="Last Name"
                    value={formData.last_name}
                    onChange={(e) => handleFieldChange('last_name', e.target.value)}
                    size="sm"
                  />
                </div>
                <div className="w-56">
                  <Input
                    label="Job Title"
                    value={formData.job_title}
                    onChange={(e) => handleFieldChange('job_title', e.target.value)}
                    size="sm"
                  />
                </div>
                <div className="w-48">
                  <Input
                    label="Company"
                    value={contact.account_name || ''}
                    size="sm"
                    readOnly
                  />
                </div>
              </div>
            ) : (
              <>
                <h2 className="text-xl font-bold text-text-primary dark:text-dark-text-primary">
                  {contact.full_name}
                </h2>
                <p className="mt-0.5 text-sm text-text-secondary dark:text-dark-text-secondary">
                  {contact.job_title || 'No title'}
                  {contact.account_name && (
                    <>
                      {' '}at{' '}
                      <span className="font-medium">{contact.account_name}</span>
                    </>
                  )}
                </p>
              </>
            )}
          </div>
          <div className="flex gap-2">
            {isEditing ? (
              <>
                <Button
                  variant="secondary"
                  size="sm"
                  icon={<Check className="h-4 w-4" />}
                  onClick={saveContact}
                  loading={updateContact.isPending}
                >
                  Save
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  icon={<X className="h-4 w-4" />}
                  onClick={cancelEditing}
                  disabled={updateContact.isPending}
                >
                  Cancel
                </Button>
              </>
            ) : (
              <>
                <Button
                  variant="secondary"
                  size="sm"
                  icon={<Edit className="h-4 w-4" />}
                  onClick={startEditing}
                >
                  Edit
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  icon={<Trash2 className="h-4 w-4" />}
                  onClick={handleDelete}
                >
                  Delete
                </Button>
              </>
            )}
          </div>
        </div>
      </Card>

      {/* Tabs */}
      <div className="border-b border-border dark:border-dark-border">
        <div className="-mb-px flex gap-0 overflow-x-auto" role="tablist">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              role="tab"
              aria-selected={activeTab === tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors whitespace-nowrap border-b-2',
                activeTab === tab.id
                  ? 'border-brand-600 text-brand-600 dark:border-brand-400 dark:text-brand-400'
                  : 'border-transparent text-text-secondary hover:text-text-primary hover:border-text-tertiary dark:text-dark-text-secondary dark:hover:text-dark-text-primary',
              )}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div role="tabpanel" aria-label={activeTab}>
        {activeTab === 'overview' && (
          <OverviewTab
            contact={contact}
            isEditing={isEditing}
            formData={formData}
            onFieldChange={handleFieldChange}
          />
        )}
        {activeTab === 'activity' && <ActivityTab contactId={contact.id} />}
        {activeTab === 'deals' && <DealsTab contactId={contact.id} />}
        {activeTab === 'notes' && <NotesTab contactId={contact.id} />}
        {activeTab === 'emails' && (
          <EmailsTab contactId={contact.id} contactEmail={contact.email} />
        )}
      </div>
    </div>
  );
}