import { useState } from 'react';
import { Modal } from './modal';
import { Button } from '../atoms/button';
import { Select } from '../atoms/select';

export interface UserOption {
  id: string;
  display_name: string;
}

export interface BulkAssignDialogProps {
  open: boolean;
  selectedCount: number;
  users: UserOption[];
  loading?: boolean;
  onAssign: (ownerId: string) => void;
  onCancel: () => void;
}

export function BulkAssignDialog({
  open,
  selectedCount,
  users,
  loading = false,
  onAssign,
  onCancel,
}: BulkAssignDialogProps) {
  const [ownerId, setOwnerId] = useState('');

  const handleCancel = () => {
    setOwnerId('');
    onCancel();
  };

  const handleConfirm = () => {
    if (!ownerId) return;
    onAssign(ownerId);
    setOwnerId('');
  };

  return (
    <Modal
      open={open}
      onClose={handleCancel}
      size="sm"
      title={`Change Owner (${selectedCount.toLocaleString()} record${selectedCount !== 1 ? 's' : ''})`}
      closeOnBackdrop={false}
      closeOnEscape={!loading}
    >
      <div className="py-2">
        <Select
          label="New Owner"
          placeholder="Select a user…"
          value={ownerId}
          onChange={(e) => setOwnerId(e.target.value)}
          disabled={loading}
        >
          {users.map((user) => (
            <option key={user.id} value={user.id}>
              {user.display_name}
            </option>
          ))}
        </Select>
      </div>

      <div className="flex items-center justify-end gap-3 pt-2">
        <Button variant="secondary" onClick={handleCancel} disabled={loading}>
          Cancel
        </Button>
        <Button variant="primary" loading={loading} disabled={!ownerId} onClick={handleConfirm}>
          Assign
        </Button>
      </div>
    </Modal>
  );
}
