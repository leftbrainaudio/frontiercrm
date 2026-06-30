import type { Meta, StoryObj } from '@storybook/react';
import { DndContext, closestCorners } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { useDroppable } from '@dnd-kit/core';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Badge } from '../../components/atoms/badge';
import { GripVertical, DollarSign, Calendar, User } from 'lucide-react';
import { cn } from '../../lib/utils';

/* ── Inline DealCard (matches the pipeline page pattern) ── */

interface Deal {
  id: string;
  name: string;
  value: number;
  contact_name?: string;
  expected_close_date?: string;
  win_probability?: number;
  currency?: string;
}

interface DealCardProps {
  deal: Deal;
}

function DealCard({ deal }: DealCardProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: deal.id,
    data: { deal, type: 'deal' },
  });

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition: transition ?? undefined,
    opacity: isDragging ? 0.4 : undefined,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="group relative rounded-lg border border-border bg-white p-3 shadow-sm hover:shadow-md hover:border-brand-300 dark:border-dark-border dark:bg-dark-surface dark:hover:border-brand-600"
    >
      <button
        type="button"
        className="absolute -left-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 cursor-grab rounded-md p-0.5 text-text-tertiary hover:text-text-primary hover:bg-surface-secondary dark:text-dark-text-tertiary dark:hover:text-dark-text-primary dark:hover:bg-dark-surface-secondary"
        {...attributes}
        {...listeners}
        aria-label="Drag to reorder"
      >
        <GripVertical className="h-4 w-4" />
      </button>
      <h4 className="text-sm font-medium text-text-primary dark:text-dark-text-primary truncate">
        {deal.name}
      </h4>
      <div className="mt-1.5 flex items-center gap-1 text-sm font-semibold text-text-primary dark:text-dark-text-primary">
        <DollarSign className="h-3.5 w-3.5 text-text-tertiary dark:text-dark-text-tertiary" />
        {new Intl.NumberFormat('en-US', { style: 'currency', currency: deal.currency || 'USD', minimumFractionDigits: 0 }).format(deal.value)}
      </div>
      {deal.contact_name && (
        <div className="mt-1 flex items-center gap-1 text-xs text-text-secondary dark:text-dark-text-secondary">
          <User className="h-3 w-3 shrink-0" />
          <span className="truncate">{deal.contact_name}</span>
        </div>
      )}
      {deal.expected_close_date && (
        <div className="mt-0.5 flex items-center gap-1 text-xs text-text-tertiary dark:text-dark-text-tertiary">
          <Calendar className="h-3 w-3 shrink-0" />
          <span>{deal.expected_close_date}</span>
        </div>
      )}
    </div>
  );
}

/* ── KanbanColumn ── */

interface Stage {
  id: string;
  name: string;
  color: string;
  display_order: number;
}

interface KanbanColumnProps {
  stage: Stage;
  deals: Deal[];
  isLoading?: boolean;
}

function KanbanColumn({ stage, deals }: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: stage.id,
    data: { stage, type: 'column' },
  });

  const totalValue = deals.reduce((sum, d) => sum + d.value, 0);

  return (
    <div
      className={cn(
        'flex shrink-0 flex-col w-[280px] rounded-xl border border-border bg-surface-secondary/50',
        'dark:border-dark-border dark:bg-dark-surface-secondary/50',
        isOver && 'ring-2 ring-brand-500/50',
      )}
    >
      <div className="flex flex-col rounded-t-xl px-3 pt-3 pb-2" style={{ borderTop: `3px solid ${stage.color}` }}>
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-text-primary dark:text-dark-text-primary truncate" style={{ color: stage.color }}>
            {stage.name}
          </h3>
          <Badge variant="neutral" size="sm">{deals.length}</Badge>
        </div>
        <div className="mt-0.5 text-xs text-text-tertiary dark:text-dark-text-tertiary">
          {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0 }).format(totalValue)}
        </div>
      </div>
      <div ref={setNodeRef} className="flex flex-col gap-2 px-3 pb-3 pt-2 min-h-[120px] flex-1 overflow-y-auto">
        <SortableContext items={deals.map((d) => d.id)} strategy={verticalListSortingStrategy}>
          {deals.map((deal) => (
            <DealCard key={deal.id} deal={deal} />
          ))}
        </SortableContext>
      </div>
    </div>
  );
}

/* ── Story ── */

const meta: Meta<typeof KanbanColumn> = {
  title: 'Organisms/KanbanColumn',
  component: KanbanColumn,
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <DndContext collisionDetection={closestCorners}>
        <div className="p-4">
          <Story />
        </div>
      </DndContext>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof KanbanColumn>;

const sampleDeals: Deal[] = [
  { id: '1', name: 'Enterprise Plan', value: 50000, contact_name: 'Alice Johnson', expected_close_date: '2026-08-15', win_probability: 80 },
  { id: '2', name: 'Pro Upgrade', value: 12000, contact_name: 'Bob Smith', expected_close_date: '2026-07-01', win_probability: 60 },
  { id: '3', name: 'Starter Package', value: 5000, contact_name: 'Carol White', expected_close_date: '2026-06-30', win_probability: 40 },
];

export const Default: Story = {
  args: {
    stage: { id: 's1', name: 'Negotiation', color: '#f59e0b', display_order: 3 },
    deals: sampleDeals,
  },
};

export const Empty: Story = {
  args: {
    stage: { id: 's2', name: 'Won', color: '#22c55e', display_order: 5 },
    deals: [],
  },
};

export const SingleDeal: Story = {
  args: {
    stage: { id: 's3', name: 'New Leads', color: '#3b82f6', display_order: 1 },
    deals: [sampleDeals[0]],
  },
};

export const WithManyDeals: Story = {
  args: {
    stage: { id: 's4', name: 'Proposal', color: '#8b5cf6', display_order: 2 },
    deals: [
      ...sampleDeals,
      { id: '4', name: 'Custom Integration', value: 25000, contact_name: 'Dan Brown' },
      { id: '5', name: 'Annual Subscription', value: 8000, expected_close_date: '2026-09-01' },
    ],
  },
};