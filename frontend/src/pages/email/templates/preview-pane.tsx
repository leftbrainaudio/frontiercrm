import { useState } from 'react';
import { Loader2, AlertTriangle } from 'lucide-react';
import { Button } from '../../../components/atoms/button';
import { Input } from '../../../components/atoms/input';
import { Badge } from '../../../components/atoms/badge';
import { usePreviewTemplate } from '../../../api/email-templates';
import DOMPurify from 'dompurify';
import type { TemplatePreview } from '../../../types';

interface PreviewPaneProps {
  subjectTemplate: string;
  bodyHtml: string;
  bodyText: string;
  templateId?: string | null;
}

export function PreviewPane({ subjectTemplate, bodyHtml, bodyText, templateId }: PreviewPaneProps) {
  const [contactId, setContactId] = useState('');
  const [dealId, setDealId] = useState('');
  const [customVars, setCustomVars] = useState('');
  const [preview, setPreview] = useState<TemplatePreview | null>(null);

  const previewMutation = usePreviewTemplate();

  const handlePreview = async () => {
    if (!templateId) {
      // Client-side preview: just show raw template
      setPreview({
        rendered_subject: subjectTemplate.replace(/\{\{(\w+)\}\}/g, '{{$1}}'),
        rendered_body_html: bodyHtml,
        rendered_body_text: bodyText,
        unresolved_variables: [],
      });
      return;
    }

    try {
      const customVariables: Record<string, string> = {};
      if (customVars.trim()) {
        customVars.split('\n').forEach((line) => {
          const [key, ...rest] = line.split(':');
          if (key && rest.length > 0) {
            customVariables[key.trim()] = rest.join(':').trim();
          }
        });
      }

      const result = await previewMutation.mutateAsync({
        id: templateId,
        context: {
          contact_id: contactId || undefined,
          deal_id: dealId || undefined,
          custom_variables: Object.keys(customVariables).length > 0 ? customVariables : undefined,
        },
      });
      setPreview(result);
    } catch {
      // Keep showing whatever we had
    }
  };

  return (
    <div className="space-y-4">
      {/* Context inputs */}
      <div className="grid grid-cols-3 gap-3">
        <Input
          label="Contact ID (optional)"
          value={contactId}
          onChange={(e) => setContactId(e.target.value)}
          placeholder="UUID"
          size="sm"
        />
        <Input
          label="Deal ID (optional)"
          value={dealId}
          onChange={(e) => setDealId(e.target.value)}
          placeholder="UUID"
          size="sm"
        />
        <div className="flex items-end">
          <Button
            variant="secondary"
            size="sm"
            onClick={handlePreview}
            loading={previewMutation.isPending}
          >
            Render Preview
          </Button>
        </div>
      </div>

      {/* Custom variables */}
      <div>
        <label className="mb-1.5 block text-xs font-medium text-text-primary dark:text-dark-text-primary">
          Custom Variables (key:value per line)
        </label>
        <textarea
          value={customVars}
          onChange={(e) => setCustomVars(e.target.value)}
          rows={2}
          className="w-full rounded-lg border border-border bg-white px-3 py-2 text-xs text-text-primary placeholder:text-text-tertiary focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary dark:placeholder:text-dark-text-tertiary"
          placeholder="proposal_url:https://example.com/proposal"
        />
      </div>

      {/* Rendered output */}
      {preview && (
        <div className="space-y-4">
          {/* Unresolved variables warning */}
          {preview.unresolved_variables.length > 0 && (
            <div className="flex items-start gap-2 rounded-lg bg-amber-50 dark:bg-amber-900/20 p-3">
              <AlertTriangle className="h-4 w-4 text-amber-500 mt-0.5 shrink-0" />
              <div>
                <p className="text-sm font-medium text-amber-800 dark:text-amber-300">
                  Unresolved Variables
                </p>
                <div className="flex flex-wrap gap-1 mt-1">
                  {preview.unresolved_variables.map((v) => (
                    <Badge key={v} size="sm" variant="warning" outline>
                      {`{{${v}}}`}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Subject */}
          <div>
            <label className="mb-1 block text-xs font-medium text-text-secondary dark:text-dark-text-secondary uppercase tracking-wide">
              Subject
            </label>
            <div className="rounded-lg border border-border dark:border-dark-border bg-white dark:bg-dark-surface px-3 py-2 text-sm text-text-primary dark:text-dark-text-primary">
              {preview.rendered_subject}
            </div>
          </div>

          {/* Body HTML */}
          <div>
            <label className="mb-1 block text-xs font-medium text-text-secondary dark:text-dark-text-secondary uppercase tracking-wide">
              HTML Preview
            </label>
            <div
              className="rounded-lg border border-border dark:border-dark-border bg-white dark:bg-dark-surface p-4 prose prose-sm max-w-none dark:prose-invert"
              dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(preview.rendered_body_html) }}
            />
          </div>

          {/* Body Text */}
          <div>
            <label className="mb-1 block text-xs font-medium text-text-secondary dark:text-dark-text-secondary uppercase tracking-wide">
              Plain Text Preview
            </label>
            <pre className="rounded-lg border border-border dark:border-dark-border bg-white dark:bg-dark-surface px-3 py-2 text-sm text-text-primary dark:text-dark-text-primary whitespace-pre-wrap font-sans">
              {preview.rendered_body_text}
            </pre>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!preview && !previewMutation.isPending && (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <p className="text-sm text-text-tertiary dark:text-dark-text-tertiary">
            Provide optional context IDs and click "Render Preview" to see the resolved template.
          </p>
        </div>
      )}

      {previewMutation.isPending && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-brand-600" />
        </div>
      )}
    </div>
  );
}