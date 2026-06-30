import { Modal } from './modal';
import { Button } from '../atoms/button';
import { AlertTriangle } from 'lucide-react';

export interface BulkConfirmDialogProps {
  open: boolean;
  title: string;
  description: string;
  selectedCount: number;
  isAllSelected: boolean;
  totalMatching?: number;
  confirmLabel?: string;
  variant?: 'danger' | 'default';
  loading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function BulkConfirmDialog({
  open,
  title,
  description,
  selectedCount,
  isAllSelected,
  totalMatching,
  confirmLabel,
  variant = 'danger',
  loading = false,
  onConfirm,
  onCancel,
}: BulkConfirmDialogProps) {
  const countLabel = isAllSelected && totalMatching
    ? totalMatching.toLocaleString()
    : selectedCount.toLocaleString();

  return (
    <Modal
      open={open}
      onClose={onCancel}
      size="sm"
      title={title}
      description={description}
      closeOnBackdrop={false}
      closeOnEscape={!loading}
    >
      {variant === 'danger' && (
        <div className="mb-4 flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-800 dark:bg-red-900/20">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
          <div>
            <p className="text-sm font-medium text-red-800 dark:text-red-300">
              This action cannot be undone.
            </p>
            <p className="mt-0.5 text-xs text-red-700 dark:text-red-400">
              {isAllSelected && totalMatching
                ? `All ${totalMatching.toLocaleString()} records matching your current filter will be affected.`
                : `${selectedCount.toLocaleString()} record${selectedCount !== 1 ? 's' : ''} will be affected.`}
            </p>
          </div>
        </div>
      )}

      <div className="flex items-center justify-end gap-3">
        <Button variant="secondary" onClick={onCancel} disabled={loading}>
          Cancel
        </Button>
        <Button
          variant={variant === 'danger' ? 'danger' : 'primary'}
          loading={loading}
          onClick={onConfirm}
        >
          {confirmLabel ?? `${variant === 'danger' ? 'Delete' : 'Confirm'} ${countLabel}`}
        </Button>
      </div>
    </Modal>
  );
}
