import { useState, useCallback, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  DndContext,
  DragOverlay,
  closestCorners,
  useSensor,
  useSensors,
  useDroppable,
  PointerSensor,
  KeyboardSensor,
  type DragStartEvent,
  type DragEndEvent,
} from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy, useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
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
  Download,
} from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { usePipelines, useDeals, useUpdateDeal, useChangeDealStatus } from '../../api/deals';
import { useCustomFieldDefs } from '../../api/custom-fields';
import type { Pipeline, Stage, Deal, DealStatus, PaginatedResponse } from '../../types';
import { cn } from '../../lib/utils';
import { Button } from '../../components/atoms/button';
import { Modal } from '../../components/molecules/modal';
import { Input } from '../../components/atoms/input';
import { AddDealModal } from '../../components/molecules/add-deal-modal';
import { Skeleton } from '../../components/atoms/skeleton';
import { Badge } from '../../components/atoms/badge';
import { Select } from '../../components/atoms/select';
import { ExportButton } from '../../components/ui/export-button';

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

/* ── Deal Custom Fields ── */

function DealCustomFieldsSection({
  customFields,
}: {
  customFields: Record<string, unknown>;
}) {
  const { data: defs } = useCustomFieldDefs('deals');

  if (!defs || defs.length === 0) return null;

  const activeDefs = defs.filter((d) => d.is_active);

  const entries = activeDefs
    .map((def) => ({
      def,
      value: customFields[def.id],
    }))
    .filter((e) => e.value !== undefined && e.value !== null && e.value !== '');

  if (entries.length === 0) return null;

  return (
    <div>
      <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary uppercase tracking-wider font-medium mb-2">
        Custom Fields
      </p>
      <div className="grid grid-cols-2 gap-3">
        {entries.map(({ def, value }) => (
          <div key={def.id}>
            <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary">
              {def.name}
            </p>
            <p className="text-sm text-text-primary dark:text-dark-text-primary mt-0.5">
              {String(value)}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
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
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: deal.id,
    data: { deal, type: 'deal' },
  });

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition: transition ?? undefined,
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
        'group relative rounded-lg border border-border bg-white p-3 shadow-sm transition-shadow transition-transform transition-opacity',
        'hover:shadow-md hover:border-brand-300',
        'dark:border-dark-border dark:bg-dark-surface dark:hover:border-brand-600',
        isDragOverlay && 'shadow-lg rotate-3 scale-105',
        isDragging ? 'cursor-grabbing scale-[0.97]' : 'cursor-pointer',
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
        'flex shrink-0 flex-col w-full md:w-[280px] rounded-xl border border-border bg-surface-secondary/50',
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
/*  Deal Detail Modal                                                          */
/* -------------------------------------------------------------------------- */

interface DealDetailProps {
  deal: Deal | null;
  open: boolean;
  onClose: () => void;
  pipelines: Pipeline[];
}

function DealDetailModal({ deal, open, onClose, pipelines }: DealDetailProps) {
  const navigate = useNavigate();
  const updateDeal = useUpdateDeal();
  const changeStatus = useChangeDealStatus();
  const queryClient = useQueryClient();

  const [isEditing, setIsEditing] = useState(false);
  const [closeReason, setCloseReason] = useState('');
  const [showCloseReason, setShowCloseReason] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Form state
  const [formName, setFormName] = useState('');
  const [formValue, setFormValue] = useState('');
  const [formStage, setFormStage] = useState('');
  const [formContactName, setFormContactName] = useState('');
  const [formCloseDate, setFormCloseDate] = useState('');

  // Reset form when deal changes or modal opens
  const prevDealId = useRef<string | null>(null);
  if (deal && deal.id !== prevDealId.current) {
    prevDealId.current = deal.id;
    setFormName(deal.name);
    setFormValue(String(deal.value));
    setFormStage(deal.stage);
    setFormContactName(deal.contact_name || '');
    setFormCloseDate(deal.expected_close_date ? deal.expected_close_date.slice(0, 10) : '');
    setIsEditing(false);
  }

  if (!deal) return null;

  const statusBadgeVariant: Record<DealStatus, 'success' | 'danger' | 'warning' | 'neutral'> = {
    open: 'success',
    won: 'success',
    lost: 'danger',
    abandoned: 'neutral',
  };

  // Find the pipeline this deal belongs to, for the stage dropdown
  const dealPipeline = pipelines.find((p) => p.id === deal.pipeline);
  const stages = (dealPipeline?.stages || []).slice().sort((a, b) => a.display_order - b.display_order);

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

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateDeal.mutateAsync({
        id: deal.id,
        name: formName.trim(),
        value: parseFloat(formValue) || 0,
        stage: formStage,
        expected_close_date: formCloseDate || null,
      });
      toast.success('Deal updated');
      queryClient.invalidateQueries({ queryKey: ['deals'] });
      queryClient.invalidateQueries({ queryKey: ['pipelines'] });
      setIsEditing(false);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to update deal';
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setFormName(deal.name);
    setFormValue(String(deal.value));
    setFormStage(deal.stage);
    setFormContactName(deal.contact_name || '');
    setFormCloseDate(deal.expected_close_date ? deal.expected_close_date.slice(0, 10) : '');
    setIsEditing(false);
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={isEditing ? 'Edit Deal' : deal.name}
      size="md"
    >
      <div className="space-y-5">
        {/* Status badge + Probability — always visible */}
        <div className="flex items-center gap-3 flex-wrap">
          <Badge variant={statusBadgeVariant[deal.status]}>{deal.status}</Badge>
          {deal.win_probability != null && (
            <span className="flex items-center gap-1 text-sm text-text-secondary dark:text-dark-text-secondary">
              <TrendingUp className="h-4 w-4" />
              {deal.win_probability}% probability
            </span>
          )}
          {!isEditing && (
            <div className="flex-1" />
          )}
          {!isEditing && (
            <Button
              size="sm"
              variant="ghost"
              icon={<Calendar className="h-4 w-4" />}
              onClick={() => {
                navigate(`/timeline?entity_type=deal&entity_id=${deal.id}`);
                onClose();
              }}
            >
              View Activities
            </Button>
          )}
        </div>

        {isEditing ? (
          /* ── EDIT MODE ── */
          <>
            <Input
              label="Deal Name"
              value={formName}
              onChange={(e) => setFormName(e.target.value)}
            />

            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Value"
                type="number"
                min={0}
                step="0.01"
                value={formValue}
                onChange={(e) => setFormValue(e.target.value)}
              />
              <Input
                label="Close Date"
                type="date"
                value={formCloseDate}
                onChange={(e) => setFormCloseDate(e.target.value)}
              />
            </div>

            <Select
              label="Pipeline Stage"
              value={formStage}
              onChange={(e) => setFormStage(e.target.value)}
            >
              {stages.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </Select>

            <Input
              label="Contact Name"
              value={formContactName}
              onChange={(e) => setFormContactName(e.target.value)}
              placeholder="Contact name"
            />

            {/* Save / Cancel */}
            <div className="flex items-center justify-end gap-3 pt-2 border-t border-border dark:border-dark-border">
              <Button variant="ghost" onClick={handleCancel} disabled={saving}>
                Cancel
              </Button>
              <Button variant="primary" onClick={handleSave} loading={saving}>
                Save Changes
              </Button>
            </div>
          </>
        ) : (
          /* ── VIEW MODE ── */
          <>
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

            {/* Custom fields */}
            <DealCustomFieldsSection customFields={deal.custom_fields} />

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
                <div className="flex-1" />
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setIsEditing(true)}
                >
                  Edit
                </Button>
              </div>
            )}

            {/* Edit button for non-open deals */}
            {deal.status !== 'open' && !showCloseReason && (
              <div className="flex items-center justify-end pt-2 border-t border-border dark:border-dark-border">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setIsEditing(true)}
                >
                  Edit
                </Button>
              </div>
            )}
          </>
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
    <div className="flex flex-col md:flex-row gap-4 overflow-x-auto pb-4 px-1">
      {Array.from({ length: 4 }).map((_, i) => (
        <div
          key={i}
          className="flex shrink-0 flex-col w-full md:w-[280px] rounded-xl border border-border bg-surface-secondary/50 p-3 dark:border-dark-border dark:bg-dark-surface-secondary/50"
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
      <div className="flex items-center gap-2">
        <ExportButton url="/export/deals/" filename="deals.csv" label="Export CSV" variant="secondary" size="sm" />
        <Button icon={<Plus className="h-4 w-4" />} onClick={onAddDeal}>
          Add Deal
        </Button>
      </div>
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

  const updateDeal = useUpdateDeal();
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
      targetStageId = (overData.deal as Deal).stage;
    }

    // Fallback: check if over id matches a pipeline stage
    if (!targetStageId) {
      const stages = activePipeline?.stages || [];
      if (stages.some((s) => s.id === over.id)) {
        targetStageId = over.id as string;
      }
    }

    if (!targetStageId || targetStageId === dealData.stage) return;

    // Find the target stage name for the optimistic update
    const targetStage = activePipeline?.stages.find((s) => s.id === targetStageId);
    const targetStageName = targetStage?.name || dealData.stage_name;

    // Optimistic update: snapshot + update ALL cached deals queries
    const cacheEntries = queryClient.getQueriesData<PaginatedResponse<Deal>>({ queryKey: ['deals'] });
    const snapshots: Array<{ key: readonly unknown[]; data: PaginatedResponse<Deal> }> = [];
    const now = new Date().toISOString();

    for (const [key, data] of cacheEntries) {
      if (!data?.results) continue;
      snapshots.push({ key, data: structuredClone(data) });
      queryClient.setQueryData<PaginatedResponse<Deal>>(key, {
        ...data,
        results: data.results.map((d) =>
          d.id === dealId
            ? { ...d, stage: targetStageId, stage_name: targetStageName, entered_stage_at: now }
            : d,
        ),
      });
    }

    try {
      await updateDeal.mutateAsync({ id: dealId, stage: targetStageId });
      toast.success('Deal moved');
      // Invalidate after success so server data (including activities) syncs
      queryClient.invalidateQueries({ queryKey: ['deals'] });
    } catch (err: unknown) {
      // Rollback every snapshot on failure
      for (const { key, data } of snapshots) {
        queryClient.setQueryData(key, data);
      }
      const msg = err instanceof Error ? err.message : 'Failed to move deal';
      toast.error(msg);
    }
  }, [activePipeline, updateDeal, queryClient]);

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

      {/* Loaded state — no pipelines exist */}
      {!isLoading && !isError && !activePipeline && pipelinesList.length === 0 && (
        <PipelineErrorState
          message="No pipelines configured yet. Contact your administrator."
        />
      )}

      {/* Loaded state — pipeline active */}
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
              <div className="flex flex-col md:flex-row gap-4 overflow-x-auto pb-4 flex-1 -mx-1 px-1">
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
      <AddDealModal
        open={addDealOpen}
        onClose={() => setAddDealOpen(false)}
        pipelines={pipelinesList}
        defaultPipelineId={activePipeline?.id}
      />

      {/* Deal Detail Modal */}
      <DealDetailModal
        deal={detailDeal}
        open={!!detailDeal}
        onClose={() => setDetailDeal(null)}
        pipelines={pipelinesList}
      />
    </div>
  );
}

export default PipelinePage;
