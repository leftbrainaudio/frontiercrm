import { useState } from 'react';
import { FileText } from 'lucide-react';
import { useEmailTemplates } from '../../../api/email-templates';
import { TemplateList } from './template-list';
import { TemplateEditor } from './template-editor';

export function EmailTemplatesPage() {
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [showNewEditor, setShowNewEditor] = useState(false);

  const params: Record<string, string> = {};
  if (search) params.search = search;
  if (categoryFilter) params.category = categoryFilter;

  const { data, isLoading, isError } = useEmailTemplates(params);
  const templates = data?.results ?? [];

  const selectedTemplate = selectedTemplateId
    ? templates.find((t) => t.id === selectedTemplateId) ?? null
    : null;

  const handleSelect = (id: string) => {
    setSelectedTemplateId(id);
    setShowNewEditor(false);
  };

  const handleNew = () => {
    setSelectedTemplateId(null);
    setShowNewEditor(true);
  };

  const handleSaved = () => {
    setSelectedTemplateId(null);
    setShowNewEditor(false);
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border dark:border-dark-border px-4 py-3">
        <div className="flex items-center gap-3">
          <FileText className="h-5 w-5 text-text-secondary dark:text-dark-text-secondary" />
          <h1 className="text-lg font-semibold text-text-primary dark:text-dark-text-primary">
            Email Templates
          </h1>
        </div>
      </div>

      {/* Content: split pane */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Template list */}
        <div className="flex w-[380px] flex-col border-r border-border dark:border-dark-border overflow-hidden">
          <TemplateList
            templates={templates}
            selectedId={selectedTemplateId}
            onSelect={handleSelect}
            onNew={handleNew}
            search={search}
            onSearchChange={setSearch}
            categoryFilter={categoryFilter}
            onCategoryFilterChange={setCategoryFilter}
            isLoading={isLoading}
            isError={isError}
          />
        </div>

        {/* Right: Editor / Empty state */}
        <div className="flex flex-1 flex-col overflow-hidden">
          {showNewEditor || selectedTemplate ? (
            <TemplateEditor
              template={selectedTemplate}
              onSaved={handleSaved}
              key={selectedTemplate?.id ?? 'new'}
            />
          ) : (
            <div className="flex flex-1 flex-col items-center justify-center text-center px-4">
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-surface-secondary dark:bg-dark-surface-secondary">
                <FileText className="h-8 w-8 text-text-tertiary dark:text-dark-text-tertiary" />
              </div>
              <h3 className="text-lg font-semibold text-text-primary dark:text-dark-text-primary">
                Select or create a template
              </h3>
              <p className="mt-1 text-sm text-text-secondary dark:text-dark-text-secondary max-w-sm">
                Choose a template from the list to edit it, or create a new one to get started.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}