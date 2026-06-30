import { useState, useEffect } from 'react';
import { Save, X, Eye, Code } from 'lucide-react';
import { Button } from '../../../components/atoms/button';
import { Input } from '../../../components/atoms/input';
import { Select } from '../../../components/atoms/select';
import { Badge } from '../../../components/atoms/badge';
import { Modal } from '../../../components/molecules/modal';
import { useEmailTemplate, useSaveTemplate, useDeleteTemplate, useTemplateVariables } from '../../../api/email-templates';
import { PreviewPane } from './preview-pane';
import toast from 'react-hot-toast';
import type { EmailTemplate } from '../../../types';

const CATEGORY_OPTIONS = [
  { value: 'general', label: 'General' },
  { value: 'introduction', label: 'Introduction' },
  { value: 'follow_up', label: 'Follow-up' },
  { value: 'meeting', label: 'Meeting Confirmation' },
  { value: 'proposal', label: 'Proposal' },
  { value: 'thank_you', label: 'Thank You' },
  { value: 'reminder', label: 'Reminder' },
  { value: 'custom', label: 'Custom' },
];

interface TemplateEditorProps {
  template: EmailTemplate | null;
  onSaved: () => void;
}

export function TemplateEditor({ template, onSaved }: TemplateEditorProps) {
  const isNew = !template;
  const [name, setName] = useState(template?.name ?? '');
  const [description, setDescription] = useState(template?.description ?? '');
  const [subjectTemplate, setSubjectTemplate] = useState(template?.subject_template ?? '');
  const [bodyHtml, setBodyHtml] = useState(template?.body_html ?? '');
  const [bodyText, setBodyText] = useState(template?.body_text ?? '');
  const [category, setCategory] = useState(template?.category ?? 'general');
  const [isShared, setIsShared] = useState(template?.is_shared ?? true);
  const [showPreview, setShowPreview] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showVariableHelp, setShowVariableHelp] = useState(false);

  // Load full detail when editing existing
  const { data: fullTemplate } = useEmailTemplate(template?.id);

  useEffect(() => {
    if (fullTemplate) {
      setName(fullTemplate.name);
      setDescription(fullTemplate.description);
      setSubjectTemplate(fullTemplate.subject_template);
      setBodyHtml(fullTemplate.body_html);
      setBodyText(fullTemplate.body_text);
      setCategory(fullTemplate.category);
      setIsShared(fullTemplate.is_shared);
    }
  }, [fullTemplate]);

  const saveTemplate = useSaveTemplate();
  const deleteTemplate = useDeleteTemplate();
  const { data: variablesData } = useTemplateVariables();

  const allVariables = variablesData?.variables ?? {};

  const handleSave = async () => {
    if (!name.trim() || !subjectTemplate.trim()) {
      toast.error('Name and subject are required');
      return;
    }
    try {
      await saveTemplate.mutateAsync({
        id: template?.id,
        name: name.trim(),
        description: description.trim(),
        subject_template: subjectTemplate.trim(),
        body_html: bodyHtml,
        body_text: bodyText,
        category,
        is_shared: isShared,
      });
      toast.success(isNew ? 'Template created' : 'Template saved');
      onSaved();
    } catch {
      toast.error('Failed to save template');
    }
  };

  const handleDelete = async () => {
    if (!template?.id) return;
    try {
      await deleteTemplate.mutateAsync(template.id);
      toast.success('Template deleted');
      setShowDeleteConfirm(false);
      onSaved();
    } catch {
      toast.error('Failed to delete template');
    }
  };

  const insertVariable = (varName: string) => {
    const tag = `{{${varName}}}`;
    setSubjectTemplate((prev) => prev + tag);
  };

  // Collect variables used
  const allContent = `${subjectTemplate} ${bodyHtml} ${bodyText}`;
  const usedVars = [...new Set(allContent.match(/\{\{(\w+)\}\}/g)?.map((m) => m.slice(2, -2)) ?? [])];

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border dark:border-dark-border px-4 py-3">
        <h2 className="text-base font-semibold text-text-primary dark:text-dark-text-primary truncate">
          {isNew ? 'New Template' : template?.name}
        </h2>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="ghost" icon={<Eye className="h-4 w-4" />} onClick={() => setShowPreview(true)}>
            Preview
          </Button>
          <Button size="sm" variant="primary" icon={<Save className="h-4 w-4" />} onClick={handleSave} loading={saveTemplate.isPending}>
            Save
          </Button>
          {!isNew && (
            <Button size="sm" variant="ghost" className="text-red-500 hover:text-red-600" onClick={() => setShowDeleteConfirm(true)}>
              Delete
            </Button>
          )}
        </div>
      </div>

      {/* Form body */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        <Input
          label="Template Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Follow-up after meeting"
          required
        />

        <div>
          <label className="mb-1.5 block text-sm font-medium text-text-primary dark:text-dark-text-primary">
            Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
            className="w-full rounded-lg border border-border bg-white px-3 py-2 text-sm text-text-primary placeholder:text-text-tertiary focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary dark:placeholder:text-dark-text-tertiary"
            placeholder="Optional description"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Select
            label="Category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            {CATEGORY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </Select>

          <div className="flex items-end pb-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={isShared}
                onChange={(e) => setIsShared(e.target.checked)}
                className="h-4 w-4 rounded border-border text-brand-600 focus:ring-brand-500"
              />
              <span className="text-sm text-text-primary dark:text-dark-text-primary">Shared with team</span>
            </label>
          </div>
        </div>

        {/* Subject with variable inserter */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-sm font-medium text-text-primary dark:text-dark-text-primary">
              Subject Template
            </label>
            <button
              type="button"
              onClick={() => setShowVariableHelp(!showVariableHelp)}
              className="text-xs text-brand-600 hover:text-brand-700 dark:text-brand-400 flex items-center gap-1"
            >
              <Code className="h-3 w-3" />
              Insert Variable
            </button>
          </div>
          <input
            type="text"
            value={subjectTemplate}
            onChange={(e) => setSubjectTemplate(e.target.value)}
            placeholder="e.g. Following up: {{deal_name}}"
            className="w-full rounded-lg border border-border bg-white px-3 py-2 text-sm text-text-primary placeholder:text-text-tertiary focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary dark:placeholder:text-dark-text-tertiary"
          />
        </div>

        {/* Variable help panel */}
        {showVariableHelp && (
          <div className="rounded-lg border border-border dark:border-dark-border p-3 bg-surface-secondary dark:bg-dark-surface-secondary max-h-48 overflow-y-auto">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-text-primary dark:text-dark-text-primary">Available Variables</span>
              <button
                type="button"
                onClick={() => setShowVariableHelp(false)}
                className="text-text-tertiary hover:text-text-primary"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
            {Object.entries(allVariables).map(([category, vars]) => (
              <div key={category} className="mb-2">
                <p className="text-xs font-medium text-text-secondary dark:text-dark-text-secondary capitalize mb-1">
                  {category}
                </p>
                <div className="flex flex-wrap gap-1">
                  {vars.map((v: any) => (
                    <button
                      key={v.name}
                      type="button"
                      onClick={() => insertVariable(v.name)}
                      className="inline-flex items-center gap-1 rounded bg-white dark:bg-dark-surface px-2 py-0.5 text-xs text-text-primary dark:text-dark-text-primary border border-border dark:border-dark-border hover:border-brand-500 transition-colors"
                      title={v.source}
                    >
                      {`{{${v.name}}}`}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Body HTML */}
        <div>
          <label className="mb-1.5 block text-sm font-medium text-text-primary dark:text-dark-text-primary">
            HTML Body
          </label>
          <textarea
            value={bodyHtml}
            onChange={(e) => setBodyHtml(e.target.value)}
            rows={8}
            className="w-full rounded-lg border border-border bg-white px-3 py-2 text-sm text-text-primary placeholder:text-text-tertiary focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary dark:placeholder:text-dark-text-tertiary font-mono"
            placeholder='<p>Hi {{contact_first_name}},</p><p>...</p>'
          />
        </div>

        {/* Body Text */}
        <div>
          <label className="mb-1.5 block text-sm font-medium text-text-primary dark:text-dark-text-primary">
            Plain Text Body
          </label>
          <textarea
            value={bodyText}
            onChange={(e) => setBodyText(e.target.value)}
            rows={5}
            className="w-full rounded-lg border border-border bg-white px-3 py-2 text-sm text-text-primary placeholder:text-text-tertiary focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary dark:placeholder:text-dark-text-tertiary font-mono"
            placeholder="Hi {{contact_first_name}},&#10;&#10;..."
          />
        </div>

        {/* Variables used display */}
        {usedVars.length > 0 && (
          <div>
            <label className="mb-1.5 block text-sm font-medium text-text-primary dark:text-dark-text-primary">
              Variables Used
            </label>
            <div className="flex flex-wrap gap-1.5">
              {usedVars.map((v) => (
                <Badge key={v} size="sm" variant="info" outline>
                  {`{{${v}}}`}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Preview modal */}
      <Modal open={showPreview} onClose={() => setShowPreview(false)} title="Template Preview" size="xl">
        <PreviewPane
          subjectTemplate={subjectTemplate}
          bodyHtml={bodyHtml}
          bodyText={bodyText}
          templateId={template?.id}
        />
      </Modal>

      {/* Delete confirmation */}
      <Modal
        open={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        title="Delete Template"
        size="sm"
        footer={
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setShowDeleteConfirm(false)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleDelete} loading={deleteTemplate.isPending}>
              Delete
            </Button>
          </div>
        }
      >
        <p className="text-sm text-text-secondary dark:text-dark-text-secondary">
          Are you sure you want to delete "{template?.name}"? This action cannot be undone.
        </p>
      </Modal>
    </div>
  );
}