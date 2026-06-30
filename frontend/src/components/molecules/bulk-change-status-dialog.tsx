import { useState } from 'react';
import { Modal } from './modal';
import { Button } from '../atoms/button';
import { Select } from '../atoms/select';
import type { DealStatus } from '../../types';

export interface BulkChangeStatusDialogProps {
  open: boolean;
  selectedCount: number;
  loading?: boolean;
  onChangeStatus: (status: string, closeReason?: string) => void;
  onCancel: () => void;
}

const STATUS_OPTIONS: { value: DealStatus; label: string }[] = [
  { value: 'won', label: 'Won' },
  { value: 'lost', label: 'Lost' },
  { value: 'abandoned', label: 'Abandoned' },
];

export function BulkChangeStatusDialog({
  open,
  selectedCount,
  loading = false,
  onChangeStatus,
  onCancel,
}: BulkChangeStatusDialogProps) {
  const [status, setStatus] = useState('');
  const [closeReason, setCloseReason] = useState('');

  const handleCancel = () => {
    setStatus('');
    setCloseReason('');
    onCancel();
  };

  const handleConfirm = () => {
    if (!status) return;
    onChangeStatus(status, closeReason || undefined);
    setStatus('');
    setCloseReason('');
  };

  return (
    <Modal
      open={open}
      onClose={handleCancel}
      size="sm"
      title={`Change Status (${selectedCount.toLocaleString()} deal${selectedCount !== 1 ? 's' : ''})`}
      closeOnBackdrop={false}
      closeOnEscape={!loading}
    >
      <div className="space-y-4 py-2">
        <Select
          label="Status"
          placeholder="Select a status…"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          disabled={loading}
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </Select>

        {(status === 'lost' || status === 'abandoned') && (
          <div>
            <label
              htmlFor="close-reason"
              className="mb-1.5 block text-sm font-medium text-text-primary dark:text-dark-text-primary"
            >
              Close Reason (optional)
            </label>
            <input
              id="close-reason"
              type="text"
              className="h-10 w-full rounded-lg border border-border px-3 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary"
              placeholder="e.g. Pricing, competitor, etc."
              value={closeReason}
              onChange={(e) => setCloseReason(e.target.value)}
              disabled={loading}
            />
          </div>
        )}
      </div>

      <div className="flex items-center justify-end gap-3 pt-2">
        <Button variant="secondary" onClick={handleCancel} disabled={loading}>
          Cancel
        </Button>
        <Button variant="primary" loading={loading} disabled={!status} onClick={handleConfirm}>
          Change Status
        </Button>
      </div>
    </Modal>
  );
}