import { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { useCreateDeal } from '../../api/deals';
import type { Pipeline } from '../../types';
import { cn } from '../../lib/utils';
import { Button } from '../atoms/button';
import { Input } from '../atoms/input';
import { Modal } from './modal';

/* -------------------------------------------------------------------------- */
/*  Add Deal Modal                                                            */
/* -------------------------------------------------------------------------- */

export interface AddDealModalProps {
  open: boolean;
  onClose: () => void;
  pipelines: Pipeline[];
  defaultPipelineId?: string;
}

export function AddDealModal({ open, onClose, pipelines, defaultPipelineId }: AddDealModalProps) {
  const createDeal = useCreateDeal();
  const queryClient = useQueryClient();

  const [name, setName] = useState('');
  const [value, setValue] = useState('');
  const [company, setCompany] = useState('');
  const [pipelineId, setPipelineId] = useState(defaultPipelineId || pipelines[0]?.id || '');
  const [stageId, setStageId] = useState('');
  const [expectedCloseDate, setExpectedCloseDate] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const selectedPipeline = pipelines.find((p) => p.id === pipelineId);
  const stages = selectedPipeline?.stages || [];

  // Reset form when modal opens
  useEffect(() => {
    if (open) {
      setName('');
      setValue('');
      setCompany('');
      setPipelineId(defaultPipelineId || pipelines[0]?.id || '');
      setStageId('');
      setExpectedCloseDate('');
      setErrors({});
    }
  }, [open, defaultPipelineId, pipelines]);

  // Auto-select first stage when pipeline changes
  const handlePipelineChange: React.ChangeEventHandler<HTMLSelectElement> = (e) => {
    const newPipelineId = e.target.value;
    setPipelineId(newPipelineId);
    const p = pipelines.find((p) => p.id === newPipelineId);
    if (p && p.stages.length > 0) {
      setStageId(p.stages[0].id);
    } else {
      setStageId('');
    }
  };

  // Initialize stage from default on first render
  useEffect(() => {
    if (!stageId && stages.length > 0) {
      setStageId(stages[0].id);
    }
  }, [stages, stageId]);

  const validate = (): boolean => {
    const errs: Record<string, string> = {};
    if (!name.trim()) errs.name = 'Deal name is required';
    if (!value.trim() || isNaN(Number(value)) || Number(value) < 0) errs.value = 'Enter a valid value';
    if (!pipelineId) errs.pipeline = 'Select a pipeline';
    if (!stageId) errs.stage = 'Select a stage';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    try {
      await createDeal.mutateAsync({
        name: name.trim(),
        value: Number(value),
        contact_name: company.trim() || undefined,
        pipeline: pipelineId,
        stage: stageId,
        expected_close_date: expectedCloseDate || undefined,
      } as any);
      toast.success('Deal created');
      queryClient.invalidateQueries({ queryKey: ['deals'] });
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create deal';
      setErrors({ form: msg });
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Add Deal" description="Create a new deal in the pipeline" size="md">
      <form onSubmit={handleSubmit} className="space-y-4">
        {errors.form && (
          <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-3">
            <p className="text-sm text-red-700 dark:text-red-400">{errors.form}</p>
          </div>
        )}

        <Input
          label="Deal Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Enterprise Contract"
          error={errors.name}
          required
        />

        <Input
          label="Value ($)"
          type="number"
          min={0}
          step="0.01"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="e.g. 50000"
          error={errors.value}
          required
        />

        <Input
          label="Company"
          value={company}
          onChange={(e) => setCompany(e.target.value)}
          placeholder="Company name"
        />

        {/* Pipeline select */}
        <div>
          <label className="mb-1.5 block text-sm font-medium text-text-primary dark:text-dark-text-primary">
            Pipeline
          </label>
          <select
            value={pipelineId}
            onChange={handlePipelineChange}
            className={cn(
              'w-full rounded-lg border border-border bg-white px-3 py-2.5 text-sm transition-colors',
              'focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500',
              'dark:bg-transparent dark:border-dark-border dark:text-dark-text-primary',
              errors.pipeline && 'border-red-500 dark:border-red-400',
            )}
            required
          >
            <option value="">Select pipeline</option>
            {pipelines.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
          {errors.pipeline && (
            <p className="mt-1 text-xs text-red-600 dark:text-red-400">{errors.pipeline}</p>
          )}
        </div>

        {/* Stage select */}
        <div>
          <label className="mb-1.5 block text-sm font-medium text-text-primary dark:text-dark-text-primary">
            Stage
          </label>
          <select
            value={stageId}
            onChange={(e) => setStageId(e.target.value)}
            className={cn(
              'w-full rounded-lg border border-border bg-white px-3 py-2.5 text-sm transition-colors',
              'focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500',
              'dark:bg-transparent dark:border-dark-border dark:text-dark-text-primary',
              errors.stage && 'border-red-500 dark:border-red-400',
            )}
            required
          >
            <option value="">Select stage</option>
            {stages.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
          {errors.stage && (
            <p className="mt-1 text-xs text-red-600 dark:text-red-400">{errors.stage}</p>
          )}
        </div>

        <Input
          label="Expected Close Date"
          type="date"
          value={expectedCloseDate}
          onChange={(e) => setExpectedCloseDate(e.target.value)}
        />

        {/* Footer buttons */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={createDeal.isPending}>
            Create Deal
          </Button>
        </div>
      </form>
    </Modal>
  );
}