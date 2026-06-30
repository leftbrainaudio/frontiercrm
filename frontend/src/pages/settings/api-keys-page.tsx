import { useState, useEffect, useRef } from 'react';
import { Key, Copy, Check, AlertTriangle, Trash2, X, Clock } from 'lucide-react';
import { useAPIKeys, useCreateAPIKey, useRevokeAPIKey, useDeleteAPIKey } from '../../api/apikeys';
import { useAuth } from '../../hooks/useAuth';
import { Button } from '../../components/atoms/button';
import { Input } from '../../components/atoms/input';
import { Modal } from '../../components/molecules/modal';
import { Card } from '../../components/molecules/card';
import { Skeleton } from '../../components/atoms/skeleton';
import { Badge } from '../../components/atoms/badge';
import toast from 'react-hot-toast';
import type { CreatedAPIKey } from '../../types';

/* ────────── Relative time helper ────────── */

function relativeTime(dateStr: string | null): string {
  if (!dateStr) return 'Never';
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = now - then;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  });
}

/* ────────── Status Badge ────────── */

function KeyStatusBadge({ isActive, revokedAt, expiresAt }: { isActive: boolean; revokedAt: string | null; expiresAt: string | null }) {
  if (revokedAt) return <Badge variant="danger">Revoked</Badge>;
  if (!isActive) return <Badge variant="neutral">Disabled</Badge>;
  if (expiresAt && new Date(expiresAt) < new Date()) return <Badge variant="warning">Expired</Badge>;
  return <Badge variant="success">Active</Badge>;
}

/* ────────── Create Key Modal ────────── */

function CreateKeyModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [name, setName] = useState('');
  const [expiresAt, setExpiresAt] = useState('');
  const [createdKey, setCreatedKey] = useState<CreatedAPIKey | null>(null);
  const [copied, setCopied] = useState(false);
  const createMutation = useCreateAPIKey();
  const keyRef = useRef<HTMLInputElement>(null);

  const handleGenerate = async () => {
    if (!name.trim()) {
      toast.error('Key name is required');
      return;
    }
    try {
      const result = await createMutation.mutateAsync({
        name: name.trim(),
        expires_at: expiresAt ? new Date(expiresAt).toISOString() : undefined,
      });
      setCreatedKey(result);
      toast.success('API key created');
    } catch {
      toast.error('Failed to create API key');
    }
  };

  const handleCopy = () => {
    if (!createdKey?.key) return;
    navigator.clipboard.writeText(createdKey.key);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleClose = () => {
    if (createdKey && !copied) {
      // Allow close without copy — user acknowledged at least once
    }
    setName('');
    setExpiresAt('');
    setCreatedKey(null);
    setCopied(false);
    onClose();
  };

  return (
    <Modal open={open} onClose={handleClose} title={createdKey ? 'API Key Created' : 'Generate New API Key'}>
      {createdKey ? (
        <div className="space-y-4">
          <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-3 dark:border-yellow-800 dark:bg-yellow-900/20">
            <div className="flex items-start gap-2">
              <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-yellow-600 dark:text-yellow-400" />
              <div>
                <p className="text-sm font-semibold text-yellow-800 dark:text-yellow-200">Copy this key now</p>
                <p className="text-xs text-yellow-600 dark:text-yellow-400">
                  You won&apos;t be able to see it again. Store it somewhere safe.
                </p>
              </div>
            </div>
          </div>

          <div className="relative">
            <Input
              ref={keyRef}
              value={createdKey.key}
              readOnly
              className="pr-24 font-mono text-xs"
            />
            <div className="absolute right-1 top-1/2 -translate-y-1/2">
              <Button size="sm" variant="outline" onClick={handleCopy}>
                {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                {copied ? 'Copied' : 'Copy'}
              </Button>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <Button onClick={handleClose}>I&apos;ve saved my key</Button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-text-primary dark:text-dark-text-primary">
              Key Name <span className="text-red-500">*</span>
            </label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. CI Pipeline"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-text-primary dark:text-dark-text-primary">
              Expires At <span className="text-xs text-text-secondary">(optional)</span>
            </label>
            <Input
              type="date"
              value={expiresAt}
              onChange={(e) => setExpiresAt(e.target.value)}
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <Button onClick={handleGenerate} disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Generating...' : 'Generate'}
            </Button>
          </div>
        </div>
      )}
    </Modal>
  );
}

/* ────────── Key Card ────────── */

function KeyCard({
  id,
  name,
  key_prefix,
  is_active,
  revoked_at,
  expires_at,
  last_used_at,
  last_ip_address,
  created_at,
}: {
  id: string;
  name: string;
  key_prefix: string;
  is_active: boolean;
  revoked_at: string | null;
  expires_at: string | null;
  last_used_at: string | null;
  last_ip_address: string | null;
  created_at: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const revokeMutation = useRevokeAPIKey();
  const deleteMutation = useDeleteAPIKey();
  const canModify = is_active && !revoked_at;

  const handleRevoke = async () => {
    if (!confirm(`Revoke API key "${name}"? This cannot be undone.`)) return;
    try {
      await revokeMutation.mutateAsync(id);
      toast.success('Key revoked');
    } catch {
      toast.error('Failed to revoke key');
    }
  };

  const handleDelete = async () => {
    if (!confirm(`Delete API key "${name}"? This cannot be undone.`)) return;
    try {
      await deleteMutation.mutateAsync(id);
      toast.success('Key deleted');
    } catch {
      toast.error('Failed to delete key');
    }
  };

  return (
    <div className="rounded-lg border border-border-primary p-4 dark:border-dark-border-primary">
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h4 className="truncate text-sm font-semibold text-text-primary dark:text-dark-text-primary">
              {name}
            </h4>
            <KeyStatusBadge isActive={is_active} revokedAt={revoked_at} expiresAt={expires_at} />
          </div>
          <p className="mt-0.5 font-mono text-xs text-text-secondary dark:text-dark-text-secondary">
            {key_prefix}...
          </p>
          <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-text-tertiary">
            <span>Created {formatDate(created_at)}</span>
            <span>Last used {relativeTime(last_used_at)}</span>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {canModify && (
            <>
              <Button size="sm" variant="outline" onClick={() => setExpanded(!expanded)}>
                Details
              </Button>
              <Button size="sm" variant="outline" className="text-red-500 hover:text-red-600" onClick={handleRevoke}>
                Revoke
              </Button>
            </>
          )}
          <Button size="sm" variant="ghost" className="text-text-tertiary hover:text-red-500" onClick={handleDelete}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {expanded && (
        <div className="mt-3 border-t border-border-primary pt-3 dark:border-dark-border-primary">
          <dl className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <dt className="text-text-tertiary dark:text-dark-text-tertiary">Last IP</dt>
              <dd className="text-text-primary dark:text-dark-text-primary">{last_ip_address || '—'}</dd>
            </div>
            <div>
              <dt className="text-text-tertiary dark:text-dark-text-tertiary">Expires</dt>
              <dd className="text-text-primary dark:text-dark-text-primary">{formatDate(expires_at)}</dd>
            </div>
            {revoked_at && (
              <div>
                <dt className="text-text-tertiary dark:text-dark-text-tertiary">Revoked</dt>
                <dd className="text-text-primary dark:text-dark-text-primary">{formatDate(revoked_at)}</dd>
              </div>
            )}
          </dl>
        </div>
      )}
    </div>
  );
}

/* ────────── Empty State ────────── */

function EmptyKeysState({ onGenerate }: { onGenerate: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-surface-secondary dark:bg-dark-surface-secondary">
        <Key className="h-6 w-6 text-text-tertiary dark:text-dark-text-tertiary" />
      </div>
      <h3 className="mb-1 text-sm font-semibold text-text-primary dark:text-dark-text-primary">
        No API keys yet
      </h3>
      <p className="mb-4 text-xs text-text-secondary dark:text-dark-text-secondary">
        Generate an API key for programmatic access to the CRM API.
      </p>
      <Button size="sm" onClick={onGenerate}>
        <Key className="mr-1.5 h-4 w-4" />
        Generate New Key
      </Button>
    </div>
  );
}

/* ────────── ApiKeysTab (exported) ────────── */

export function ApiKeysTab() {
  const [modalOpen, setModalOpen] = useState(false);
  const { data: keys, isLoading, error } = useAPIKeys();
  const { user } = useAuth();

  if (isLoading) {
    return (
      <div className="space-y-3 p-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} width="100%" height={72} />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <p className="text-sm text-red-500">Failed to load API keys.</p>
      </div>
    );
  }

  return (
    <div className="p-4">
      {/* Header */}
      {keys && keys.length > 0 && (
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-text-primary dark:text-dark-text-primary">
              API Keys
            </h3>
            <p className="text-xs text-text-secondary dark:text-dark-text-secondary">
              Manage keys for programmatic access to the FrontierCRM API.
            </p>
          </div>
          <Button size="sm" onClick={() => setModalOpen(true)}>
            <Key className="mr-1.5 h-4 w-4" />
            Generate New Key
          </Button>
        </div>
      )}

      {/* Key list or empty state */}
      {keys && keys.length > 0 ? (
        <div className="space-y-2">
          {keys.map((key) => (
            <KeyCard key={key.id} {...key} />
          ))}
        </div>
      ) : !isLoading ? (
        <EmptyKeysState onGenerate={() => setModalOpen(true)} />
      ) : null}

      {/* Create modal */}
      <CreateKeyModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}
