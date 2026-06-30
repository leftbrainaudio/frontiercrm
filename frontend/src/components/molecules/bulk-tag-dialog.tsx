import { useState, useCallback } from 'react';
import { Modal } from './modal';
import { Button } from '../atoms/button';
import { Tag } from '../atoms/tag';
import { Plus } from 'lucide-react';

export interface BulkTagDialogProps {
  open: boolean;
  title: string;
  selectedCount: number;
  actionLabel: string;
  loading?: boolean;
  onApplyTags: (tags: string[]) => void;
  onCancel: () => void;
}

export function BulkTagDialog({
  open,
  title,
  selectedCount,
  actionLabel,
  loading = false,
  onApplyTags,
  onCancel,
}: BulkTagDialogProps) {
  const [tags, setTags] = useState<string[]>([]);
  const [inputValue, setInputValue] = useState('');

  const handleCancel = () => {
    setTags([]);
    setInputValue('');
    onCancel();
  };

  const addTag = useCallback(() => {
    const trimmed = inputValue.trim();
    if (trimmed && !tags.includes(trimmed)) {
      setTags((prev) => [...prev, trimmed]);
    }
    setInputValue('');
  }, [inputValue, tags]);

  const removeTag = useCallback((tag: string) => {
    setTags((prev) => prev.filter((t) => t !== tag));
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addTag();
    }
  };

  const handleConfirm = () => {
    if (tags.length === 0) {
      // If no tags added, proceed with empty array
      onApplyTags([]);
    } else {
      onApplyTags(tags);
    }
    setTags([]);
    setInputValue('');
  };

  return (
    <Modal
      open={open}
      onClose={handleCancel}
      size="sm"
      title={`${title} (${selectedCount.toLocaleString()} record${selectedCount !== 1 ? 's' : ''})`}
      closeOnBackdrop={false}
      closeOnEscape={!loading}
    >
      <div className="py-2">
        {/* Tag display */}
        {tags.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-1.5">
            {tags.map((tag) => (
              <Tag key={tag} variant="default" size="md" onRemove={() => removeTag(tag)}>
                {tag}
              </Tag>
            ))}
          </div>
        )}

        {/* Tag input */}
        <div className="flex gap-2">
          <input
            type="text"
            className="h-10 flex-1 rounded-lg border border-border px-3 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary"
            placeholder="Type a tag and press Enter…"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />
          <Button
            variant="secondary"
            size="sm"
            icon={<Plus className="h-4 w-4" />}
            onClick={addTag}
            disabled={loading || !inputValue.trim()}
          >
            Add
          </Button>
        </div>
      </div>

      <div className="flex items-center justify-end gap-3 pt-2">
        <Button variant="secondary" onClick={handleCancel} disabled={loading}>
          Cancel
        </Button>
        <Button
          variant="primary"
          loading={loading}
          disabled={tags.length === 0}
          onClick={handleConfirm}
        >
          {actionLabel}
        </Button>
      </div>
    </Modal>
  );
}
