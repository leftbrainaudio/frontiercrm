import { useState } from 'react';
import { FileText, AlertTriangle, ChevronDown } from 'lucide-react';
import { Button } from '../../../components/atoms/button';
import { Badge } from '../../../components/atoms/badge';
import { useEmailTemplates, usePreviewTemplate } from '../../../api/email-templates';
import type { TemplatePreview } from '../../../types';

interface TemplatePickerProps {
  onApplyTemplate: (rendered: {
    subject: string;
    bodyHtml: string;
    bodyText: string;
    templateId: string;
    templateName: string;
  }) => void;
  contextContactId?: string;
  contextDealId?: string;
  disabled?: boolean;
}

export function TemplatePicker({
  onApplyTemplate,
  contextContactId,
  contextDealId,
  disabled,
}: TemplatePickerProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [preview, setPreview] = useState<TemplatePreview | null>(null);
  const [isApplying, setIsApplying] = useState(false);
  const [open, setOpen] = useState(false);

  const { data: templatesData, isLoading: templatesLoading } = useEmailTemplates({ is_shared: 'true' });
  const previewMutation = usePreviewTemplate();

  const templates = templatesData?.results ?? [];
  const selectedTemplate = templates.find((t) => t.id === selectedId) ?? null;

  const handleSelect = (id: string) => {
    setSelectedId(id);
    setPreview(null);
    setOpen(false);
  };

  const handleApply = async () => {
    if (!selectedId) return;
    setIsApplying(true);
    try {
      const result = await previewMutation.mutateAsync({
        id: selectedId,
        context: {
          contact_id: contextContactId,
          deal_id: contextDealId,
        },
      });
      setPreview(result);
      onApplyTemplate({
        subject: result.rendered_subject,
        bodyHtml: result.rendered_body_html,
        bodyText: result.rendered_body_text,
        templateId: selectedId,
        templateName: selectedTemplate?.name ?? '',
      });
    } finally {
      setIsApplying(false);
    }
  };

  return (
    <div className="space-y-2">
      {/* Dropdown */}
      <div className="relative">
        <label className="mb-1 block text-xs font-medium text-text-secondary dark:text-dark-text-secondary uppercase tracking-wide">
          Template
        </label>
        <button
          type="button"
          onClick={() => setOpen(!open)}
          disabled={disabled || templatesLoading}
          className="flex w-full items-center justify-between rounded-lg border border-border dark:border-dark-border bg-white dark:bg-dark-surface px-3 py-2 text-sm text-text-primary dark:text-dark-text-primary hover:border-brand-500 transition-colors disabled:opacity-60"
        >
          <span className={selectedTemplate ? '' : 'text-text-tertiary'}>
            {selectedTemplate ? selectedTemplate.name : templatesLoading ? 'Loading...' : templates.length === 0 ? 'No templates' : 'Select a template...'}
          </span>
          <ChevronDown className="h-4 w-4 text-text-tertiary" />
        </button>

        {open && (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
            <div className="absolute left-0 right-0 top-full mt-1 z-20 rounded-lg border border-border dark:border-dark-border bg-white dark:bg-dark-surface shadow-lg max-h-48 overflow-y-auto">
              {templates.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => handleSelect(t.id)}
                  className="w-full text-left px-3 py-2 text-sm text-text-primary dark:text-dark-text-primary hover:bg-surface-secondary dark:hover:bg-dark-surface-secondary transition-colors"
                >
                  <span className="font-medium">{t.name}</span>
                  <span className="ml-2 text-xs text-text-tertiary">{t.category.replace(/_/g, ' ')}</span>
                </button>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Selected template details */}
      {selectedTemplate && (
        <div className="rounded-lg border border-border dark:border-dark-border p-2.5 bg-surface-secondary dark:bg-dark-surface-secondary">
          <div className="flex items-center justify-between">
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-text-primary dark:text-dark-text-primary truncate">
                {selectedTemplate.name}
              </p>
              {selectedTemplate.variables_used.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {selectedTemplate.variables_used.map((v) => (
                    <Badge key={v} size="sm" variant="info" outline>
                      {`{{${v}}}`}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
            <Button
              size="sm"
              variant="primary"
              onClick={handleApply}
              loading={isApplying}
              disabled={disabled}
            >
              Apply
            </Button>
          </div>
        </div>
      )}

      {/* Unresolved warning */}
      {preview && preview.unresolved_variables.length > 0 && (
        <div className="flex items-start gap-2 text-xs text-amber-600 dark:text-amber-400">
          <AlertTriangle className="h-3 w-3 mt-0.5 shrink-0" />
          <span>
            {preview.unresolved_variables.length} variable{preview.unresolved_variables.length !== 1 ? 's' : ''} could not be resolved
            {contextContactId || contextDealId ? ' with the current context.' : '. Select a contact/deal first for auto-resolution.'}
          </span>
        </div>
      )}

      {/* Empty state */}
      {!templatesLoading && templates.length === 0 && (
        <div className="flex items-center gap-2 text-xs text-text-tertiary dark:text-dark-text-tertiary">
          <FileText className="h-3 w-3" />
          <span>No templates yet. Create one in Email Templates.</span>
        </div>
      )}
    </div>
  );
}