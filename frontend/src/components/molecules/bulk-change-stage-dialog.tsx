import { useState } from 'react';
import { Modal } from './modal';
import { Button } from '../atoms/button';
import { Select } from '../atoms/select';
import type { Pipeline } from '../../types';

export interface BulkChangeStageDialogProps {
  open: boolean;
  selectedCount: number;
  pipelines: Pipeline[];
  loading?: boolean;
  onChangeStage: (stageId: string) => void;
  onCancel: () => void;
}

export function BulkChangeStageDialog({
  open,
  selectedCount,
  pipelines,
  loading = false,
  onChangeStage,
  onCancel,
}: BulkChangeStageDialogProps) {
  const [pipelineId, setPipelineId] = useState('');
  const [stageId, setStageId] = useState('');

  const selectedPipeline = pipelines.find((p) => p.id === pipelineId);
  const stages = selectedPipeline?.stages ?? [];

  const handleCancel = () => {
    setPipelineId('');
    setStageId('');
    onCancel();
  };

  const handleConfirm = () => {
    if (!stageId) return;
    onChangeStage(stageId);
    setPipelineId('');
    setStageId('');
  };

  return (
    <Modal
      open={open}
      onClose={handleCancel}
      size="sm"
      title={`Move to Stage (${selectedCount.toLocaleString()} deal${selectedCount !== 1 ? 's' : ''})`}
      closeOnBackdrop={false}
      closeOnEscape={!loading}
    >
      <div className="space-y-4 py-2">
        <Select
          label="Pipeline"
          placeholder="Select a pipeline…"
          value={pipelineId}
          onChange={(e) => {
            setPipelineId(e.target.value);
            setStageId('');
          }}
          disabled={loading}
        >
          {pipelines.filter((p) => p.is_active !== false).map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </Select>

        <Select
          label="Stage"
          placeholder="Select a stage…"
          value={stageId}
          onChange={(e) => setStageId(e.target.value)}
          disabled={loading || !pipelineId}
        >
          {stages
            .filter((s) => s.is_active !== false)
            .sort((a, b) => a.display_order - b.display_order)
            .map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
        </Select>
      </div>

      <div className="flex items-center justify-end gap-3 pt-2">
        <Button variant="secondary" onClick={handleCancel} disabled={loading}>
          Cancel
        </Button>
        <Button variant="primary" loading={loading} disabled={!stageId} onClick={handleConfirm}>
          Move
        </Button>
      </div>
    </Modal>
  );
}
