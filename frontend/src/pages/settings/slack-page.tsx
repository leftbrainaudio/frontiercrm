import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Plus,
  X,
  RefreshCw,
  MessageSquare,
  AlertCircle,
  Trash2,
  TestTube,
} from 'lucide-react';
import { Button } from '../../components/atoms/button';
import { Input } from '../../components/atoms/input';
import { Badge } from '../../components/atoms/badge';
import { Card } from '../../components/molecules/card';
import { Modal } from '../../components/molecules/modal';
import { Skeleton } from '../../components/atoms/skeleton';
import { cn } from '../../lib/utils';
import toast from 'react-hot-toast';
import {
  useSlackWebhooks,
  useCreateSlackWebhook,
  useUpdateSlackWebhook,
  useDeleteSlackWebhook,
  useTestSlackWebhook,
  useDeactivateSlackWebhook,
  usePipelinesList,
  type SlackWebhook,
  type SlackWebhookCreate,
  getEventLabel,
  DEFAULT_SUBSCRIBED_EVENTS,
} from '../../api/slack';

const ALL_EVENT_TYPES = [
  'deal_stage_change',
  'deal_status_change',
  'email',
  'note',
  'call',
  'meeting',
  'task',
  'file_upload',
];

/* ────────── Skeleton ────────── */

function SlackSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 2 }).map((_, i) => (
        <Skeleton key={i} width="100%" height={120} />
      ))}
    </div>
  );
}

/* ────────── Empty State ────────── */

function EmptyState({ onAdd }: { onAdd: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-surface-secondary dark:bg-dark-surface-secondary">
        <MessageSquare className="h-8 w-8 text-text-tertiary dark:text-dark-text-tertiary" />
      </div>
      <h3 className="text-lg font-semibold text-text-primary dark:text-dark-text-primary">
        No Slack webhooks configured
      </h3>
      <p className="mt-1 text-sm text-text-secondary dark:text-dark-text-secondary">
        Connect a Slack channel to receive CRM notifications.
      </p>
      <Button icon={<Plus className="h-4 w-4" />} className="mt-6" onClick={onAdd}>
        Add Slack Webhook
      </Button>
    </div>
  );
}

/* ────────── Error State ────────── */

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-50 dark:bg-red-900/20">
        <AlertCircle className="h-6 w-6 text-red-500 dark:text-red-400" />
      </div>
      <p className="text-sm text-text-secondary dark:text-dark-text-secondary">{message}</p>
      <Button variant="outline" size="sm" icon={<RefreshCw className="h-4 w-4" />} className="mt-4" onClick={onRetry}>
        Retry
      </Button>
    </div>
  );
}

/* ────────── Slack Webhook Form (Add/Edit) ────────── */

interface SlackWebhookFormProps {
  open: boolean;
  onClose: () => void;
  initial?: SlackWebhook;
}

function SlackWebhookForm({ open, onClose, initial }: SlackWebhookFormProps) {
  const createWebhook = useCreateSlackWebhook();
  const updateWebhook = useUpdateSlackWebhook();
  const { data: pipelines } = usePipelinesList();
  const isEdit = !!initial;

  const [webhookUrl, setWebhookUrl] = useState(initial?.webhook_url || '');
  const [displayName, setDisplayName] = useState(initial?.display_name || '');
  const [channelOverride, setChannelOverride] = useState(initial?.channel_override || '');
  const [selectedEvents, setSelectedEvents] = useState<string[]>(
    initial?.subscribed_events?.length ? initial.subscribed_events : DEFAULT_SUBSCRIBED_EVENTS,
  );
  const [pipelineFilterId, setPipelineFilterId] = useState<string>(
    initial?.pipeline_filter?.id || '',
  );
  const [urlError, setUrlError] = useState('');

  const toggleEvent = (event: string) => {
    setSelectedEvents((prev) =>
      prev.includes(event) ? prev.filter((e) => e !== event) : [...prev, event],
    );
  };

  const handleSubmit = async () => {
    setUrlError('');

    if (!webhookUrl.trim()) {
      setUrlError('Webhook URL is required');
      return;
    }
    if (!webhookUrl.startsWith('https://hooks.slack.com/services/')) {
      setUrlError('Must be a valid Slack Incoming Webhook URL');
      return;
    }

    const payload: SlackWebhookCreate = {
      webhook_url: webhookUrl.trim(),
      display_name: displayName.trim() || undefined,
      channel_override: channelOverride.trim() || undefined,
      subscribed_events: selectedEvents,
      pipeline_filter_id: pipelineFilterId || null,
    };

    try {
      if (isEdit && initial) {
        await updateWebhook.mutateAsync({ id: initial.id, ...payload });
        toast.success('Slack webhook updated');
      } else {
        await createWebhook.mutateAsync(payload);
        toast.success('Slack webhook connected');
      }
      onClose();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || err?.response?.data?.webhook_url?.[0] || 'Failed to save webhook');
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={isEdit ? 'Edit Slack Webhook' : 'Add Slack Webhook'}
      description={
        isEdit ? 'Update your Slack webhook configuration.' : 'Connect a Slack channel to receive CRM notifications.'
      }
      size="md"
      footer={
        <div className="flex gap-3">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            loading={createWebhook.isPending || updateWebhook.isPending}
            disabled={!webhookUrl.trim()}
          >
            {isEdit ? 'Save Changes' : 'Connect'}
          </Button>
        </div>
      }
    >
      <div className="space-y-4">
        <Input
          label="Webhook URL"
          value={webhookUrl}
          onChange={(e) => {
            setWebhookUrl(e.target.value);
            setUrlError('');
          }}
          placeholder="https://hooks.slack.com/services/..."
          error={urlError}
          required
        />
        <Input
          label="Display Name"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          placeholder="e.g. Sales Team Channel"
          helperText="Optional friendly label"
        />
        <Input
          label="Channel Override"
          value={channelOverride}
          onChange={(e) => setChannelOverride(e.target.value)}
          placeholder="e.g. #sales-team"
          helperText="Leave empty to use the webhook's default channel"
        />

        {/* Event subscriptions */}
        <div>
          <label className="mb-1.5 block text-sm font-medium text-text-primary dark:text-dark-text-primary">
            Send Notifications For
          </label>
          <div className="grid grid-cols-2 gap-2">
            {ALL_EVENT_TYPES.map((event) => (
              <label
                key={event}
                className={cn(
                  'flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm transition-colors',
                  'hover:bg-surface-secondary dark:hover:bg-dark-surface-secondary',
                  selectedEvents.includes(event)
                    ? 'border-brand-500 bg-brand-50 dark:border-brand-400 dark:bg-brand-900/20'
                    : 'border-border dark:border-dark-border',
                )}
              >
                <input
                  type="checkbox"
                  checked={selectedEvents.includes(event)}
                  onChange={() => toggleEvent(event)}
                  className="h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                />
                <span className="text-text-primary dark:text-dark-text-primary">{getEventLabel(event)}</span>
              </label>
            ))}
          </div>
          <p className="mt-1.5 text-xs text-text-tertiary dark:text-dark-text-tertiary">
            Leave all unchecked = receive all events
          </p>
        </div>

        {/* Pipeline filter */}
        <div>
          <label className="mb-1.5 block text-sm font-medium text-text-primary dark:text-dark-text-primary">
            Pipeline Filter
          </label>
          <select
            value={pipelineFilterId}
            onChange={(e) => setPipelineFilterId(e.target.value)}
            className="w-full rounded-lg border border-border bg-white px-3 py-2.5 text-sm text-text-primary focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary"
          >
            <option value="">All Pipelines</option>
            {(pipelines ?? []).map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <p className="mt-1.5 text-xs text-text-tertiary dark:text-dark-text-tertiary">
            Only notify on deals in this pipeline (optional)
          </p>
        </div>
      </div>
    </Modal>
  );
}

/* ────────── Slack Webhook Card ────────── */

type SlackWebhookCardProps = {
  webhook: SlackWebhook;
  onEdit: (wh: SlackWebhook) => void;
};

function SlackWebhookCard({ webhook, onEdit }: SlackWebhookCardProps) {
  const testWebhook = useTestSlackWebhook();
  const deactivateWebhook = useDeactivateSlackWebhook();
  const updateWebhook = useUpdateSlackWebhook();
  const deleteWebhook = useDeleteSlackWebhook();
  const [confirmDelete, setConfirmDelete] = useState(false);

  const handleTest = async () => {
    try {
      const result: any = await testWebhook.mutateAsync(webhook.id);
      if (result.status === 'delivered') {
        toast.success('Test message sent successfully!');
      } else {
        toast.error(result.error || 'Test message failed');
      }
    } catch (err: any) {
      toast.error(err?.response?.data?.error || 'Test message failed');
    }
  };

  const handleDeactivate = async () => {
    try {
      await deactivateWebhook.mutateAsync(webhook.id);
      toast.success('Webhook deactivated');
    } catch {
      toast.error('Failed to deactivate webhook');
    }
  };

  const handleReactivate = async () => {
    try {
      await updateWebhook.mutateAsync({ id: webhook.id, is_active: true });
      toast.success('Webhook reactivated');
    } catch {
      toast.error('Failed to reactivate webhook');
    }
  };

  const handleDelete = async () => {
    try {
      await deleteWebhook.mutateAsync(webhook.id);
      toast.success('Webhook removed');
    } catch {
      toast.error('Failed to remove webhook');
    }
  };

  const displayEvents = webhook.subscribed_events?.length
    ? webhook.subscribed_events
    : ['all'];

  return (
    <Card variant="interactive" padding="md" className="space-y-3">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-semibold text-text-primary dark:text-dark-text-primary">
              {webhook.display_name || 'Slack Webhook'}
            </h4>
            {webhook.is_active ? (
              <Badge variant="success" size="sm">
                Active
              </Badge>
            ) : (
              <Badge variant="warning" size="sm">
                ⚠️ Deactivated{webhook.failure_count >= 10 ? ` (${webhook.failure_count} failures)` : ''}
              </Badge>
            )}
          </div>
          {webhook.channel_override && (
            <p className="mt-0.5 text-xs text-text-secondary dark:text-dark-text-secondary">
              Channel: {webhook.channel_override}
            </p>
          )}
        </div>
      </div>

      {/* Event badges */}
      <div className="flex flex-wrap gap-1.5">
        {displayEvents.map((evt) => (
          <Badge key={evt} variant="info" size="sm">
            {evt === 'all' ? 'All Events' : getEventLabel(evt)}
          </Badge>
        ))}
      </div>

      {webhook.pipeline_filter && (
        <p className="text-xs text-text-secondary dark:text-dark-text-secondary">
          Filtered to pipeline: {webhook.pipeline_filter.name}
        </p>
      )}

      {webhook.last_triggered_at && (
        <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary">
          Last triggered: {new Date(webhook.last_triggered_at).toLocaleString()}
        </p>
      )}

      {/* Actions */}
      <div className="flex flex-wrap items-center gap-2 pt-1">
        <Button
          size="sm"
          variant="secondary"
          icon={<TestTube className="h-3.5 w-3.5" />}
          onClick={handleTest}
          loading={testWebhook.isPending}
        >
          Test
        </Button>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => onEdit(webhook)}
        >
          Edit
        </Button>
        {webhook.is_active ? (
          <Button
            size="sm"
            variant="ghost"
            onClick={handleDeactivate}
            loading={deactivateWebhook.isPending}
          >
            Deactivate
          </Button>
        ) : (
          <Button
            size="sm"
            variant="ghost"
            onClick={handleReactivate}
            loading={updateWebhook.isPending}
          >
            Reactivate
          </Button>
        )}
        {confirmDelete ? (
          <div className="flex items-center gap-1">
            <Button
              size="sm"
              variant="danger"
              onClick={handleDelete}
            >
              Confirm Remove
            </Button>
            <button
              type="button"
              onClick={() => setConfirmDelete(false)}
              className="rounded p-1 text-text-tertiary hover:text-text-primary transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <Button
            size="sm"
            variant="ghost"
            icon={<Trash2 className="h-3.5 w-3.5" />}
            onClick={() => setConfirmDelete(true)}
          >
            Remove
          </Button>
        )}
      </div>
    </Card>
  );
}

/* ────────── Slack Settings Page ────────── */

export function SlackSettingsPage() {
  const navigate = useNavigate();
  const { data: webhooks, isLoading, isError, error, refetch } = useSlackWebhooks();
  const [showForm, setShowForm] = useState(false);
  const [editingWebhook, setEditingWebhook] = useState<SlackWebhook | undefined>(undefined);

  const handleEdit = (wh: SlackWebhook) => {
    setEditingWebhook(wh);
    setShowForm(true);
  };

  const handleAdd = () => {
    setEditingWebhook(undefined);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingWebhook(undefined);
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6 lg:px-8">
      {/* Page header */}
      <div className="mb-6">
        <button
          type="button"
          onClick={() => navigate('/settings')}
          className="mb-3 inline-flex items-center gap-1 text-sm text-text-secondary hover:text-text-primary transition-colors dark:text-dark-text-secondary dark:hover:text-dark-text-primary"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Settings
        </button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-text-primary dark:text-dark-text-primary">
              Slack Integration
            </h1>
            <p className="mt-1 text-sm text-text-secondary dark:text-dark-text-secondary">
              Send CRM notifications to your Slack channels.
            </p>
          </div>
          {webhooks && webhooks.length > 0 && (
            <Button icon={<Plus className="h-4 w-4" />} onClick={handleAdd}>
              Add Webhook
            </Button>
          )}
        </div>
      </div>

      {/* Content */}
      {isLoading ? (
        <SlackSkeleton />
      ) : isError ? (
        <ErrorState
          message={(error as any)?.message || 'Failed to load Slack webhooks'}
          onRetry={() => refetch()}
        />
      ) : !webhooks || webhooks.length === 0 ? (
        <EmptyState onAdd={handleAdd} />
      ) : (
        <div className="space-y-4">
          {webhooks.map((wh) => (
            <SlackWebhookCard
              key={wh.id}
              webhook={wh}
              onEdit={handleEdit}
            />
          ))}
        </div>
      )}

      {/* Setup instructions */}
      <div className="mt-8 rounded-xl border border-border dark:border-dark-border p-5">
        <h3 className="text-sm font-semibold text-text-primary dark:text-dark-text-primary">
          Need a webhook URL?
        </h3>
        <ol className="mt-2 ml-4 list-decimal space-y-1 text-sm text-text-secondary dark:text-dark-text-secondary">
          <li>Open Slack → Apps → Incoming Webhooks</li>
          <li>Add to a channel → Copy the webhook URL</li>
          <li>Paste it in the form above</li>
        </ol>
      </div>

      {/* Add/Edit form modal */}
      <SlackWebhookForm
        open={showForm}
        onClose={handleFormClose}
        initial={editingWebhook}
      />
    </div>
  );
}