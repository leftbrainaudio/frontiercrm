import { useState, useCallback, useMemo } from 'react';
import {
  DndContext,
  DragOverlay,
  closestCorners,
  useSensor,
  useSensors,
  useDroppable,
  useDraggable,
  PointerSensor,
  KeyboardSensor,
  type DragStartEvent,
  type DragEndEvent,
} from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import {
  Plus,
  GripVertical,
  DollarSign,
  Calendar,
  User,
  CheckCircle2,
  XCircle,
  Archive,
  TrendingUp,
} from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { usePipelines, useDeals, useCreateDeal, useMoveDealStage, useChangeDealStatus } from '../../api/deals';
import type { Pipeline, Stage, Deal, DealStatus } from '../../types';
import { cn } from '../../lib/utils';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Modal } from '../../components/ui/modal';
import { Skeleton } from '../../components/ui/skeleton';
import { Badge } from '../../components/ui/badge';

/* -------------------------------------------------------------------------- */
/*  Helpers                                                                    */
/* -------------------------------------------------------------------------- */

function formatCurrency(value: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  try {
    return format(parseISO(dateStr), 'MMM d, yyyy');
  } catch {
    return dateStr;
  }
}

function getStageColor(stage: Stage, dark = false): string {
  if (dark) {
    // Dark-mode variants for the colour bar
    const darkMap: Record<string, string> = {
      red: '#ef4444',
      orange: '#f97316',
      amber: '#f59e0b',
      yellow: '#eab308',
      lime: '#84cc16',
      green: '#22c55e',
      emerald: '#10b981',
      teal: '#14b8a6',
      cyan: '#06b6d4',
      sky: '#0ea5e9',
      blue: '#3b82f6',
      indigo: '#6366f1',
      violet: '#8b5cf6',
      purple: '#a855f7',
      fuchsia: '#d946ef',
      pink: '#ec4899',
      rose: '#f43f5e',
    };
    const color = stage.color?.toLowerCase() || '';
    for (const [key, val] of Object.entries(darkMap)) {
      if (color.includes(key)) return val;
    }
    return stage.color || '#6366f1';
  }
  return stage.color || '#6366f1';
}

/* -------------------------------------------------------------------------- */
/*  Deal Card (draggable)                                                      */
/* -------------------------------------------------------------------------- */

interface DealCardProps {
  deal: Deal;
  onClick: (deal: Deal) => void;
  isDragOverlay?: boolean;
}

function DealCard({ deal, onClick, isDragOverlay }: DealCardProps) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: deal.id,
    data: { deal, type: 'deal' },
  });

  const style: React.CSSProperties = {
    transform: transform ? `translate3d(${transform.x}px, ${transform.y}px, 0)` : undefined,
    opacity: isDragging ? 0.4 : undefined,
    zIndex: isDragging ? 999 : undefined,
  };

  const stageColor = deal.win_probability != null
    ? deal.win_probability >= 80
      ? '#22c55e'
      : deal.win_probability >= 50
        ? '#f59e0b'
        : deal.win_probability >= 20
          ? '#f97316'
          : '#ef4444'
    : undefined;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        'group relative rounded-lg border border-border bg-white p-3 shadow-sm transition-shadow',
        'hover:shadow-md hover:border-brand-300',
        'dark:border-dark-border dark:bg-dark-surface dark:hover:border-brand-600',
        isDragOverlay && 'shadow-lg rotate-3 scale-105',
        isDragging ? 'cursor-grabbing' : 'cursor-pointer',
      )}
      onClick={() => !isDragging && onClick(deal)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter') onClick(deal); }}
      aria-label={`Deal: ${deal.name}`}
    >
      {/* Drag handle */}
      <button
        type="button"
        className={cn(
          'absolute -left-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity',
          'cursor-grab rounded-md p-0.5 text-text-tertiary hover:text-text-primary hover:bg-surface-secondary',
          'dark:text-dark-text-tertiary dark:hover:text-dark-text-primary dark:hover:bg-dark-surface-secondary',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
        )}
        {...attributes}
        {...listeners}
        aria-label="Drag to reorder"
      >
        <GripVertical className="h-4 w-4" />
      </button>

      {/* Top row: Name + probability bar */}
      <div className="flex items-start justify-between gap-2">
        <h4 className="text-sm font-medium text-text-primary dark:text-dark-text-primary truncate flex-1">
          {deal.name}
        </h4>
        {deal.win_probability != null && (
          <span
            className="shrink-0 text-xs font-semibold rounded-full px-1.5 py-0.5"
            style={{
              backgroundColor: `${stageColor}20`,
              color: stageColor,
            }}
          >
            {deal.win_probability}%
          </span>
        )}
      </div>

      {/* Value */}
      <div className="mt-1.5 flex items-center gap-1 text-sm font-semibold text-text-primary dark:text-dark-text-primary">
        <DollarSign className="h-3.5 w-3.5 text-text-tertiary dark:text-dark-text-tertiary" />
        {formatCurrency(deal.value, deal.currency)}
      </div>

      {/* Contact */}
      {deal.contact_name && (
        <div className="mt-1 flex items-center gap-1 text-xs text-text-secondary dark:text-dark-text-secondary">
          <User className="h-3 w-3 shrink-0" />
          <span className="truncate">{deal.contact_name}</span>
        </div>
      )}

      {/* Close date */}
      {deal.expected_close_date && (
        <div className="mt-0.5 flex items-center gap-1 text-xs text-text-tertiary dark:text-dark-text-tertiary">
          <Calendar className="h-3 w-3 shrink-0" />
          <span>{formatDate(deal.expected_close_date)}</span>
        </div>
      )}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Deal Card Skeleton                                                         */
/* -------------------------------------------------------------------------- */

function DealCardSkeleton() {
  return (
    <div className="rounded-lg border border-border bg-white p-3 dark:border-dark-border dark:bg-dark-surface">
      <Skeleton width="70%" height={16} className="mb-2" />
      <Skeleton width="50%" height={14} className="mb-1.5" />
      <Skeleton width="60%" height={12} />
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Kanban Column (droppable)                                                  */
/* -------------------------------------------------------------------------- */

interface KanbanColumnProps {
  stage: Stage;
  deals: Deal[];
  onDealClick: (deal: Deal) => void;
  isLoading?: boolean;
}

function KanbanColumn({ stage, deals, onDealClick, isLoading }: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: stage.id,
    data: { stage, type: 'column' },
  });

  const totalValue = deals.reduce((sum, d) => sum + d.value, 0);
  const color = getStageColor(stage);

  return (
    <div
      className={cn(
        'flex shrink-0 flex-col w-[280px] rounded-xl border border-border bg-surface-secondary/50',
        'dark:border-dark-border dark:bg-dark-surface-secondary/50',
        isOver && 'ring-2 ring-brand-500/50 bg-brand-50/30 dark:bg-brand-900/10',
      )}
    >
      {/* Column header with color bar */}
      <div
        className="flex flex-col rounded-t-xl px-3 pt-3 pb-2"
        style={{ borderTop: `3px solid ${color}` }}
      >
        <div className="flex items-center justify-between">
          <h3
            className="text-sm font-semibold text-text-primary dark:text-dark-text-primary truncate"
            style={{ color }}
          >
            {stage.name}
          </h3>
          <Badge variant="neutral" size="sm">
            {deals.length}
          </Badge>
        </div>
        <div className="mt-0.5 text-xs text-text-tertiary dark:text-dark-text-tertiary">
          {formatCurrency(totalValue)}
        </div>
      </div>

      {/* Deal cards */}
      <div
        ref={setNodeRef}
        className="flex flex-col gap-2 overflow-y-auto px-3 pb-3 pt-2 min-h-[120px] flex-1"
      >
        {isLoading ? (
          <>
            <DealCardSkeleton />
            <DealCardSkeleton />
            <DealCardSkeleton />
          </>
        ) : deals.length === 0 ? (
          <div className="flex items-center justify-center h-full py-8">
            <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary text-center">
              No deals
            </p>
          </div>
        ) : (
          <SortableContext items={deals.map((d) => d.id)} strategy={verticalListSortingStrategy}>
            {deals.map((deal) => (
              <DealCard key={deal.id} deal={deal} onClick={onDealClick} />
            ))}
          </SortableContext>
        )}
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Pipeline Tabs                                                              */
/* -------------------------------------------------------------------------- */

interface PipelineTabsProps {
  pipelines: Pipeline[];
  selected: string;
  onChange: (id: string) => void;
}

function PipelineTabs({ pipelines, selected, onChange }: PipelineTabsProps) {
  return (
    <div className="flex gap-0.5 rounded-lg bg-surface-secondary p-0.5 dark:bg-dark-surface-secondary">
      {pipelines.map((p) => (
        <button
          key={p.id}
          type="button"
          onClick={() => onChange(p.id)}
          className={cn(
            'rounded-md px-3 py-1.5 text-sm font-medium transition-all duration-150',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
            selected === p.id
              ? 'bg-white text-text-primary shadow-sm dark:bg-dark-surface dark:text-dark-text-primary'
              : 'text-text-secondary hover:text-text-primary dark:text-dark-text-secondary dark:hover:text-dark-text-primary',
          )}
          aria-pressed={selected === p.id}
        >
          {p.name}
        </button>
      ))}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Add Deal Form                                                              */
/* -------------------------------------------------------------------------- */

interface AddDealFormProps {
  pipelines: Pipeline[];
  defaultPipelineId?: string;
  onSuccess: () => void;
  onCancel: () => void;
}

function AddDealForm({ pipelines, defaultPipelineId, onSuccess, onCancel }: AddDealFormProps) {
  const createDeal = useCreateDeal();
  const [name, setName] = useState('');
  const [value, setValue] = useState('');
  const [contact, setContact] = useState('');
  const [pipelineId, setPipelineId] = useState(defaultPipelineId || pipelines[0]?.id || '');
  const [stageId, setStageId] = useState('');
  const [expectedCloseDate, setExpectedCloseDate] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const selectedPipeline = pipelines.find((p) => p.id === pipelineId);
  const stages = selectedPipeline?.stages || [];

  // Auto-select first stage when pipeline changes
  const handlePipelineChange: React.ChangeEventHandler<HTMLSelectElement> = (e) => {
    setPipelineId(e.target.value);
    const p = pipelines.find((p) => p.id === e.target.value);
    if (p && p.stages.length > 0) {
      setStageId(p.stages[0].id);
    } else {
      setStageId('');
    }
  };

  // Initialize stage from default
  useState(() => {
    if (!stageId && stages.length > 0) {
      setStageId(stages[0].id);
    }
  });

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
        contact_name: contact.trim() || undefined,
        pipeline: pipelineId,
        stage: stageId,
        expected_close_date: expectedCloseDate || undefined,
      } as any);
      toast.success('Deal created');
      onSuccess();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create deal';
      toast.error(msg);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
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
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="e.g. 50000"
        error={errors.value}
        required
      />

      <Input
        label="Contact"
        value={contact}
        onChange={(e) => setContact(e.target.value)}
        placeholder="Contact name"
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
          onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setStageId(e.target.value)}
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

      {/* Footer buttons via Modal footer slot */}
      <div className="flex items-center justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={createDeal.isPending}>
          Create Deal
        </Button>
      </div>
    </form>
  );
}

/* -------------------------------------------------------------------------- */
/*  Deal Detail Modal                                                          */
/* -------------------------------------------------------------------------- */

interface DealDetailProps {
  deal: Deal | null;
  open: boolean;
  onClose: () => void;
}

function DealDetailModal({ deal, open, onClose }: DealDetailProps) {
  const changeStatus = useChangeDealStatus();
  const queryClient = useQueryClient();
  const [closeReason, setCloseReason] = useState('');
  const [showCloseReason, setShowCloseReason] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  if (!deal) return null;

  const statusBadgeVariant: Record<DealStatus, 'success' | 'danger' | 'warning' | 'neutral'> = {
    open: 'success',
    won: 'success',
    lost: 'danger',
    abandoned: 'neutral',
  };

  const handleStatusChange = async (status: DealStatus) => {
    if (status === 'lost' && !closeReason.trim()) {
      setShowCloseReason(true);
      return;
    }
    setActionLoading(status);
    try {
      await changeStatus.mutateAsync({
        id: deal.id,
        status,
        close_reason: status === 'lost' ? closeReason.trim() || undefined : undefined,
      });
      toast.success(`Deal marked as ${status}`);
      queryClient.invalidateQueries({ queryKey: ['pipelines'] });
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to update deal status';
      toast.error(msg);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={deal.name}
      size="md"
    >
      <div className="space-y-5">
        {/* Status badge + Probability */}
        <div className="flex items-center gap-3 flex-wrap">
          <Badge variant={statusBadgeVariant[deal.status]}>{deal.status}</Badge>
          {deal.win_probability != null && (
            <span className="flex items-center gap-1 text-sm text-text-secondary dark:text-dark-text-secondary">
              <TrendingUp className="h-4 w-4" />
              {deal.win_probability}% probability
            </span>
          )}
        </div>

        {/* Value */}
        <div className="bg-surface-secondary dark:bg-dark-surface-secondary rounded-lg p-4">
          <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary uppercase tracking-wider font-medium">
            Deal Value
          </p>
          <p className="text-2xl font-bold text-text-primary dark:text-dark-text-primary mt-1">
            {formatCurrency(deal.value, deal.currency)}
          </p>
        </div>

        {/* Details grid */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary uppercase tracking-wider font-medium">
              Pipeline
            </p>
            <p className="text-sm text-text-primary dark:text-dark-text-primary mt-0.5">
              {deal.pipeline_name}
            </p>
          </div>
          <div>
            <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary uppercase tracking-wider font-medium">
              Stage
            </p>
            <p className="text-sm text-text-primary dark:text-dark-text-primary mt-0.5">
              {deal.stage_name}
            </p>
          </div>
          <div>
            <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary uppercase tracking-wider font-medium">
              Contact
            </p>
            <p className="text-sm text-text-primary dark:text-dark-text-primary mt-0.5">
              {deal.contact_name || '—'}
            </p>
          </div>
          <div>
            <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary uppercase tracking-wider font-medium">
              Expected Close
            </p>
            <p className="text-sm text-text-primary dark:text-dark-text-primary mt-0.5">
              {formatDate(deal.expected_close_date)}
            </p>
          </div>
          <div>
            <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary uppercase tracking-wider font-medium">
              Account
            </p>
            <p className="text-sm text-text-primary dark:text-dark-text-primary mt-0.5">
              {deal.account_name || '—'}
            </p>
          </div>
          <div>
            <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary uppercase tracking-wider font-medium">
              Owner
            </p>
            <p className="text-sm text-text-primary dark:text-dark-text-primary mt-0.5">
              {deal.owner_id || '—'}
            </p>
          </div>
        </div>

        {/* Description */}
        {deal.description && (
          <div>
            <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary uppercase tracking-wider font-medium mb-1">
              Description
            </p>
            <p className="text-sm text-text-primary dark:text-dark-text-primary whitespace-pre-wrap">
              {deal.description}
            </p>
          </div>
        )}

        {/* Close reason input */}
        {showCloseReason && (
          <div>
            <Input
              label="Close Reason"
              value={closeReason}
              onChange={(e) => setCloseReason(e.target.value)}
              placeholder="e.g. Budget, Competitor, Timing..."
            />
            <div className="mt-2 flex gap-2">
              <Button
                size="sm"
                variant="danger"
                loading={actionLoading === 'lost'}
                onClick={() => handleStatusChange('lost')}
              >
                Confirm Lost
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setShowCloseReason(false)}>
                Cancel
              </Button>
            </div>
          </div>
        )}

        {/* Status change actions */}
        {deal.status === 'open' && !showCloseReason && (
          <div className="flex items-center gap-3 pt-2 border-t border-border dark:border-dark-border">
            <Button
              size="sm"
              variant="primary"
              icon={<CheckCircle2 className="h-4 w-4" />}
              loading={actionLoading === 'won'}
              onClick={() => handleStatusChange('won')}
            >
              Mark Won
            </Button>
            <Button
              size="sm"
              variant="danger"
              icon={<XCircle className="h-4 w-4" />}
              loading={actionLoading === 'lost'}
              onClick={() => handleStatusChange('lost')}
            >
              Mark Lost
            </Button>
            <Button
              size="sm"
              variant="ghost"
              icon={<Archive className="h-4 w-4" />}
              onClick={() => handleStatusChange('abandoned')}
            >
              Abandon
            </Button>
          </div>
        )}
      </div>
    </Modal>
  );
}

/* -------------------------------------------------------------------------- */
/*  Empty State                                                                */
/* -------------------------------------------------------------------------- */

function EmptyPipelineState({ pipelineName }: { pipelineName: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-4">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-surface-secondary dark:bg-dark-surface-secondary">
        <TrendingUp className="h-8 w-8 text-text-tertiary dark:text-dark-text-tertiary" />
      </div>
      <h3 className="text-lg font-semibold text-text-primary dark:text-dark-text-primary">
        No deals yet
      </h3>
      <p className="mt-1 text-sm text-text-secondary dark:text-dark-text-secondary text-center max-w-sm">
        There are no deals in <strong>{pipelineName}</strong> yet. Start by adding your first deal.
      </p>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Error State                                                                */
/* -------------------------------------------------------------------------- */

function PipelineErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-4">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-50 dark:bg-red-900/20">
        <XCircle className="h-8 w-8 text-red-500" />
      </div>
      <h3 className="text-lg font-semibold text-text-primary dark:text-dark-text-primary">
        Failed to load pipeline
      </h3>
      <p className="mt-1 text-sm text-text-secondary dark:text-dark-text-secondary text-center max-w-sm">
        {message}
      </p>
      {onRetry && (
        <Button variant="secondary" className="mt-4" onClick={onRetry}>
          Try Again
        </Button>
      )}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Loading State                                                              */
/* -------------------------------------------------------------------------- */

function PipelineLoadingState() {
  return (
    <div className="flex gap-4 overflow-x-auto pb-4 px-1">
      {Array.from({ length: 4 }).map((_, i) => (
        <div
          key={i}
          className="flex shrink-0 flex-col w-[280px] rounded-xl border border-border bg-surface-secondary/50 p-3 dark:border-dark-border dark:bg-dark-surface-secondary/50"
        >
          <Skeleton width="60%" height={18} className="mb-1" />
          <Skeleton width="40%" height={12} className="mb-4" />
          <div className="flex flex-col gap-2">
            <DealCardSkeleton />
            <DealCardSkeleton />
            <DealCardSkeleton />
          </div>
        </div>
      ))}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Pipeline Header Stats                                                      */
/* -------------------------------------------------------------------------- */

function PipelineHeader({
  pipeline,
  deals,
  onAddDeal,
}: {
  pipeline: Pipeline | undefined;
  deals: Deal[];
  onAddDeal: () => void;
}) {
  if (!pipeline) return null;

  const totalValue = deals.reduce((sum, d) => sum + d.value, 0);

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold text-text-primary dark:text-dark-text-primary">
          {pipeline.name}
        </h1>
        <div className="flex items-center gap-4 mt-1">
          <span className="text-sm text-text-secondary dark:text-dark-text-secondary">
            {deals.length} deal{deals.length !== 1 ? 's' : ''}
          </span>
          <span className="text-sm font-semibold text-text-primary dark:text-dark-text-primary">
            {formatCurrency(totalValue)}
          </span>
        </div>
      </div>
      <Button icon={<Plus className="h-4 w-4" />} onClick={onAddDeal}>
        Add Deal
      </Button>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Main Pipeline Page                                                         */
/* -------------------------------------------------------------------------- */

export function PipelinePage() {
  const { data: pipelines, isLoading: pipelinesLoading, isError: pipelinesError, refetch: refetchPipelines } = usePipelines();
  const [selectedPipelineId, setSelectedPipelineId] = useState<string | undefined>(undefined);

  // Fetch deals with pipeline filter
  const pipelineFilter = selectedPipelineId ? { pipeline: selectedPipelineId } : undefined;
  const { data: dealsData, isLoading: dealsLoading, isError: dealsError, refetch: refetchDeals } = useDeals(pipelineFilter);

  const moveStage = useMoveDealStage();
  const queryClient = useQueryClient();

  // Active pipeline
  const pipelinesList = pipelines || [];
  const activePipeline = useMemo(
    () => pipelinesList.find((p) => p.id === selectedPipelineId) || pipelinesList[0],
    [pipelinesList, selectedPipelineId],
  );

  // Sync selected pipeline id on first load
  useState(() => {
    if (!selectedPipelineId && pipelinesList.length > 0) {
      setSelectedPipelineId(pipelinesList[0].id);
    }
  });

  // Active deals list
  const dealsList = dealsData?.results || [];

  // Group deals by stage
  const dealsByStage = useMemo(() => {
    const map = new Map<string, Deal[]>();
    (activePipeline?.stages || []).forEach((s) => map.set(s.id, []));
    dealsList.forEach((deal) => {
      if (map.has(deal.stage)) {
        map.get(deal.stage)!.push(deal);
      }
    });
    return map;
  }, [dealsList, activePipeline]);

  // DnD sensors
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 8 },
    }),
    useSensor(KeyboardSensor),
  );

  // Drag state
  const [activeDeal, setActiveDeal] = useState<Deal | null>(null);

  // Modal state
  const [addDealOpen, setAddDealOpen] = useState(false);
  const [detailDeal, setDetailDeal] = useState<Deal | null>(null);

  const handleDragStart = useCallback((event: DragStartEvent) => {
    const deal = event.active.data.current?.deal as Deal | undefined;
    if (deal) {
      setActiveDeal(deal);
    }
  }, []);

  const handleDragEnd = useCallback(async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveDeal(null);

    if (!over) return;

    const dealId = active.id as string;
    const dealData = active.data.current?.deal as Deal | undefined;
    if (!dealData) return;

    // Determine the target stage id
    const overData = over.data.current;
    let targetStageId: string | undefined;

    if (overData?.type === 'column') {
      targetStageId = over.id as string;
    } else if (overData?.deal) {
      const overDeal = overData.deal as Deal;
      targetStageId = overDeal.stage;
    } else if (overData?.type === 'deal') {
      targetStageId = (overData.deal as Deal).stage;
    }

    // If the stage actually has the stage id as a key (SortableContext items are deal ids)
    // Check if the over id is a stage id (matches one of our pipeline stages)
    if (!targetStageId) {
      const stages = activePipeline?.stages || [];
      if (stages.some((s) => s.id === over.id)) {
        targetStageId = over.id as string;
      }
    }

    if (!targetStageId || targetStageId === dealData.stage) return;

    try {
      await moveStage.mutateAsync({ id: dealId, stage_id: targetStageId });
      queryClient.invalidateQueries({ queryKey: ['deals'] });
      toast.success('Deal moved');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to move deal';
      toast.error(msg);
    }
  }, [activePipeline, moveStage, queryClient]);

  const handleAddDealSuccess = useCallback(() => {
    setAddDealOpen(false);
    queryClient.invalidateQueries({ queryKey: ['deals'] });
  }, [queryClient]);

  const handlePipelineChange = useCallback((id: string) => {
    setSelectedPipelineId(id);
  }, []);

  const isLoading = pipelinesLoading || dealsLoading;
  const isError = pipelinesError || dealsError;
  const errorMessage = 'Something went wrong loading the pipeline.';

  // Build a sorted deals list for the active pipeline
  const sortedStages = useMemo(() => {
    return (activePipeline?.stages || [])
      .slice()
      .sort((a, b) => a.display_order - b.display_order);
  }, [activePipeline]);

  return (
    <div className="h-full flex flex-col gap-6 p-4 sm:p-6 lg:p-8">
      {/* Pipeline selector */}
      {pipelinesList.length > 1 && (
        <PipelineTabs
          pipelines={pipelinesList}
          selected={activePipeline?.id || ''}
          onChange={handlePipelineChange}
        />
      )}

      {/* Loading state */}
      {isLoading && !pipelinesError && (
        <>
          <div className="h-12" aria-hidden="true" />
          <PipelineLoadingState />
        </>
      )}

      {/* Error state */}
      {isError && !isLoading && (
        <PipelineErrorState
          message={errorMessage}
          onRetry={() => {
            refetchPipelines();
            refetchDeals();
          }}
        />
      )}

      {/* Loaded state */}
      {!isLoading && !isError && activePipeline && (
        <>
          <PipelineHeader
            pipeline={activePipeline}
            deals={dealsList}
            onAddDeal={() => setAddDealOpen(true)}
          />

          {/* Empty state */}
          {dealsList.length === 0 ? (
            <EmptyPipelineState pipelineName={activePipeline.name} />
          ) : (
            /* Kanban Board */
            <DndContext
              sensors={sensors}
              collisionDetection={closestCorners}
              onDragStart={handleDragStart}
              onDragEnd={handleDragEnd}
            >
              <div className="flex gap-4 overflow-x-auto pb-4 flex-1 -mx-1 px-1">
                {sortedStages.map((stage) => (
                  <KanbanColumn
                    key={stage.id}
                    stage={stage}
                    deals={dealsByStage.get(stage.id) || []}
                    onDealClick={(deal) => setDetailDeal(deal)}
                    isLoading={false}
                  />
                ))}
              </div>

              {/* Drag Overlay */}
              <DragOverlay>
                {activeDeal ? (
                  <div className="w-[280px]">
                    <DealCard deal={activeDeal} onClick={() => {}} isDragOverlay />
                  </div>
                ) : null}
              </DragOverlay>
            </DndContext>
          )}
        </>
      )}

      {/* Add Deal Modal */}
      <Modal
        open={addDealOpen}
        onClose={() => setAddDealOpen(false)}
        title="Add Deal"
        description="Create a new deal in the pipeline"
        size="md"
      >
        <AddDealForm
          pipelines={pipelinesList}
          defaultPipelineId={activePipeline?.id}
          onSuccess={handleAddDealSuccess}
          onCancel={() => setAddDealOpen(false)}
        />
      </Modal>

      {/* Deal Detail Modal */}
      <DealDetailModal
        deal={detailDeal}
        open={!!detailDeal}
        onClose={() => setDetailDeal(null)}
      />
    </div>
  );
}

export default PipelinePage;