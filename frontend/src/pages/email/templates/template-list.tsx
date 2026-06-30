import { Search, Plus, FileText, AlertCircle } from 'lucide-react';
import { Button } from '../../../components/atoms/button';
import { Badge } from '../../../components/atoms/badge';
import { Select } from '../../../components/atoms/select';
import { Skeleton } from '../../../components/atoms/skeleton';
import { cn } from '../../../lib/utils';
import type { EmailTemplate } from '../../../types';

const CATEGORY_OPTIONS = [
  { value: '', label: 'All Categories' },
  { value: 'general', label: 'General' },
  { value: 'introduction', label: 'Introduction' },
  { value: 'follow_up', label: 'Follow-up' },
  { value: 'meeting', label: 'Meeting Confirmation' },
  { value: 'proposal', label: 'Proposal' },
  { value: 'thank_you', label: 'Thank You' },
  { value: 'reminder', label: 'Reminder' },
  { value: 'custom', label: 'Custom' },
];

const CATEGORY_BADGE: Record<string, string> = {
  introduction: 'info',
  follow_up: 'warning',
  meeting: 'success',
  proposal: 'default',
  thank_you: 'success',
  reminder: 'warning',
  custom: 'neutral',
  general: 'neutral',
};

interface TemplateListProps {
  templates: EmailTemplate[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  search: string;
  onSearchChange: (v: string) => void;
  categoryFilter: string;
  onCategoryFilterChange: (v: string) => void;
  isLoading: boolean;
  isError: boolean;
}

export function TemplateList({
  templates,
  selectedId,
  onSelect,
  onNew,
  search,
  onSearchChange,
  categoryFilter,
  onCategoryFilterChange,
  isLoading,
  isError,
}: TemplateListProps) {
  return (
    <div className="flex h-full flex-col">
      {/* Search + new button */}
      <div className="flex items-center gap-2 border-b border-border dark:border-dark-border px-3 py-3">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-text-tertiary dark:text-dark-text-tertiary pointer-events-none" />
          <input
            type="text"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search templates..."
            className="w-full rounded-lg border border-border bg-white pl-8 pr-3 py-1.5 text-sm text-text-primary placeholder:text-text-tertiary focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary dark:placeholder:text-dark-text-tertiary"
          />
        </div>
        <Button size="sm" icon={<Plus className="h-4 w-4" />} onClick={onNew}>
          New
        </Button>
      </div>

      {/* Category filter */}
      <div className="px-3 py-2 border-b border-border dark:border-dark-border">
        <Select
          size="sm"
          value={categoryFilter}
          onChange={(e) => onCategoryFilterChange(e.target.value)}
        >
          {CATEGORY_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </Select>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto divide-y divide-border dark:divide-dark-border">
        {isLoading ? (
          <div className="space-y-2 p-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="space-y-2 p-2">
                <Skeleton width="70%" height={16} />
                <Skeleton width="40%" height={12} />
              </div>
            ))}
          </div>
        ) : isError ? (
          <div className="flex flex-col items-center justify-center py-16 text-center px-4">
            <AlertCircle className="h-8 w-8 text-red-400 mb-2" />
            <p className="text-sm text-text-secondary dark:text-dark-text-secondary">
              Failed to load templates
            </p>
          </div>
        ) : templates.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center px-4">
            <FileText className="h-8 w-8 text-text-tertiary dark:text-dark-text-tertiary mb-2" />
            <p className="text-sm text-text-secondary dark:text-dark-text-secondary">
              {search || categoryFilter
                ? 'No templates match your filters'
                : 'No templates yet'}
            </p>
          </div>
        ) : (
          templates.map((t) => (
            <TemplateCard
              key={t.id}
              template={t}
              selected={t.id === selectedId}
              onClick={() => onSelect(t.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}

interface TemplateCardProps {
  template: EmailTemplate;
  selected: boolean;
  onClick: () => void;
}

function TemplateCard({ template, selected, onClick }: TemplateCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'w-full text-left transition-colors px-3 py-2.5',
        selected && 'bg-brand-50 dark:bg-brand-900/20',
        !selected && 'hover:bg-surface-secondary dark:hover:bg-dark-surface-secondary',
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p
            className={cn(
              'text-sm truncate',
              selected
                ? 'font-semibold text-text-primary dark:text-dark-text-primary'
                : 'font-medium text-text-primary dark:text-dark-text-primary',
            )}
          >
            {template.name}
          </p>
          <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary truncate mt-0.5">
            {template.description || 'No description'}
          </p>
          <div className="flex items-center gap-2 mt-1.5">
            <Badge
              size="sm"
              variant={(CATEGORY_BADGE[template.category] as any) || 'neutral'}
            >
              {template.category.replace(/_/g, ' ')}
            </Badge>
            {template.variables_used.length > 0 && (
              <span className="text-xs text-text-tertiary dark:text-dark-text-tertiary">
                {template.variables_used.length} var{template.variables_used.length !== 1 ? 's' : ''}
              </span>
            )}
          </div>
        </div>
      </div>
    </button>
  );
}