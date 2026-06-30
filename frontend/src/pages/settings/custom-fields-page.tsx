import { useState } from 'react';
import {
  Plus,
  Edit,
  Trash2,
  AlertCircle,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { Button } from '../../components/atoms/button';
import { Card } from '../../components/molecules/card';
import { Input } from '../../components/atoms/input';
import { Modal } from '../../components/molecules/modal';
import { Badge } from '../../components/atoms/badge';
import { Skeleton } from '../../components/atoms/skeleton';
import {
  useCustomFieldDefs,
  useCreateCustomFieldDef,
  useUpdateCustomFieldDef,
  useDeleteCustomFieldDef,
} from '../../api/custom-fields';
import type { CustomFieldDef, CustomFieldType, CustomFieldEntity } from '../../types';

const FIELD_TYPE_LABELS: Record<CustomFieldType, string> = {
  text: 'Text',
  number: 'Number',
  date: 'Date',
  select: 'Select',
};

const ENTITY_TYPE_LABELS: Record<CustomFieldEntity, string> = {
  contacts: 'Contacts',
  deals: 'Deals',
  accounts: 'Accounts',
};

const FIELD_TYPES: CustomFieldType[] = ['text', 'number', 'date', 'select'];
const ENTITY_TYPES: CustomFieldEntity[] = ['contacts', 'deals', 'accounts'];

interface FieldFormData {
  name: string;
  field_type: CustomFieldType;
  entity_type: CustomFieldEntity;
  options: string;
  order: number;
}

const emptyForm: FieldFormData = {
  name: '',
  field_type: 'text',
  entity_type: 'contacts',
  options: '',
  order: 0,
};

/* ── Colour mapping for field-type badges ── */

const typeBadgeVariant: Record<CustomFieldType, 'default' | 'neutral' | 'success' | 'warning'> = {
  text: 'default',
  number: 'neutral',
  date: 'success',
  select: 'warning',
};

/* ── Form Component ── */

function FieldForm({
  data,
  onChange,
}: {
  data: FieldFormData;
  onChange: (d: FieldFormData) => void;
}) {
  return (
    <div className="space-y-4">
      <Input
        label="Field Name"
        value={data.name}
        onChange={(e) => onChange({ ...data, name: e.target.value })}
        placeholder="e.g. Industry Vertical"
        required
      />

      {/* Field Type */}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-text-primary dark:text-dark-text-primary">
          Field Type
        </label>
        <select
          value={data.field_type}
          onChange={(e) => onChange({ ...data, field_type: e.target.value as CustomFieldType })}
          className="w-full rounded-lg border border-border bg-white px-3 py-2.5 text-sm text-text-primary focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary"
        >
          {FIELD_TYPES.map((t) => (
            <option key={t} value={t}>
              {FIELD_TYPE_LABELS[t]}
            </option>
          ))}
        </select>
      </div>

      {/* Entity Type */}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-text-primary dark:text-dark-text-primary">
          Applies To
        </label>
        <select
          value={data.entity_type}
          onChange={(e) => onChange({ ...data, entity_type: e.target.value as CustomFieldEntity })}
          className="w-full rounded-lg border border-border bg-white px-3 py-2.5 text-sm text-text-primary focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary"
        >
          {ENTITY_TYPES.map((t) => (
            <option key={t} value={t}>
              {ENTITY_TYPE_LABELS[t]}
            </option>
          ))}
        </select>
      </div>

      {/* Options (only for select type) */}
      {data.field_type === 'select' && (
        <Input
          label="Options (one per line)"
          value={data.options}
          onChange={(e) => onChange({ ...data, options: e.target.value })}
          placeholder="Option A\nOption B\nOption C"
          helperText="Enter each option on a separate line"
        />
      )}
    </div>
  );
}

/* ── Main Custom Fields Settings Tab ── */

export default function CustomFieldsSettingsPage() {
  const { data: fields, isLoading, isError, error } = useCustomFieldDefs();
  const createField = useCreateCustomFieldDef();
  const updateField = useUpdateCustomFieldDef();
  const deleteField = useDeleteCustomFieldDef();

  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<FieldFormData>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const resetForm = () => {
    setForm(emptyForm);
    setEditingId(null);
  };

  const openCreate = () => {
    resetForm();
    setModalOpen(true);
  };

  const openEdit = (f: CustomFieldDef) => {
    setForm({
      name: f.name,
      field_type: f.field_type,
      entity_type: f.entity_type,
      options: (f.options ?? []).join('\n'),
      order: f.order,
    });
    setEditingId(f.id);
    setModalOpen(true);
  };

  const handleSave = async () => {
    if (!form.name.trim()) {
      toast.error('Field name is required');
      return;
    }

    setSaving(true);
    try {
      const payload: Record<string, unknown> = {
        name: form.name.trim(),
        field_type: form.field_type,
        entity_type: form.entity_type,
        order: form.order,
      };

      if (form.field_type === 'select') {
        payload.options = form.options
          .split('\n')
          .map((s) => s.trim())
          .filter(Boolean);
      } else {
        payload.options = [];
      }

      if (editingId) {
        await updateField.mutateAsync({ id: editingId, ...payload } as any);
        toast.success('Custom field updated');
      } else {
        await createField.mutateAsync(payload as any);
        toast.success('Custom field created');
      }

      setModalOpen(false);
      resetForm();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to save custom field');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteField.mutateAsync(id);
      toast.success('Custom field deleted');
      setDeleteConfirm(null);
    } catch {
      toast.error('Failed to delete custom field');
    }
  };

  /* ── Group by entity type ── */

  const grouped = fields?.reduce(
    (acc, f) => {
      const key = f.entity_type;
      if (!acc[key]) acc[key] = [];
      acc[key].push(f);
      return acc;
    },
    {} as Record<string, CustomFieldDef[]>,
  );

  /* ── Loading state ── */

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton width="100%" height={48} />
        <Skeleton width="100%" height={48} />
        <Skeleton width="100%" height={48} />
      </div>
    );
  }

  /* ── Error state ── */

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-50 dark:bg-red-900/20">
          <AlertCircle className="h-6 w-6 text-red-500" />
        </div>
        <p className="text-sm text-text-secondary dark:text-dark-text-secondary">
          {(error as any)?.message || 'Failed to load custom fields'}
        </p>
      </div>
    );
  }

  const totalCount = fields?.length ?? 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-text-primary dark:text-dark-text-primary">
            Custom Fields
          </h3>
          <p className="text-sm text-text-secondary dark:text-dark-text-secondary">
            {totalCount} field{totalCount !== 1 ? 's' : ''} defined
          </p>
        </div>
        <Button icon={<Plus className="h-4 w-4" />} onClick={openCreate}>
          Add Field
        </Button>
      </div>

      {/* Empty state */}
      {totalCount === 0 ? (
        <Card>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <p className="text-sm text-text-tertiary dark:text-dark-text-tertiary">
              No custom fields defined yet. Add fields to capture extra data on contacts, deals, or accounts.
            </p>
          </div>
        </Card>
      ) : (
        /* Field lists grouped by entity */
        <div className="space-y-6">
          {ENTITY_TYPES.map((entity) => {
            const entityFields = grouped?.[entity] ?? [];
            if (entityFields.length === 0) return null;

            return (
              <div key={entity}>
                <h4 className="mb-2 text-sm font-semibold text-text-primary dark:text-dark-text-primary">
                  {ENTITY_TYPE_LABELS[entity]}
                </h4>
                <div className="divide-y divide-border dark:divide-dark-border rounded-xl border border-border dark:border-dark-border">
                  {entityFields.map((f) => (
                    <div key={f.id} className="flex items-center gap-4 px-4 py-3">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-text-primary dark:text-dark-text-primary truncate">
                          {f.name}
                        </p>
                        <div className="mt-0.5 flex items-center gap-2">
                          <Badge variant={typeBadgeVariant[f.field_type]} size="sm">
                            {FIELD_TYPE_LABELS[f.field_type]}
                          </Badge>
                          {!f.is_active && (
                            <span className="text-xs text-text-tertiary dark:text-dark-text-tertiary">
                              Inactive
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        <button
                          type="button"
                          onClick={() => openEdit(f)}
                          className="rounded-lg p-2 text-text-tertiary hover:text-text-primary hover:bg-surface-secondary dark:hover:bg-dark-surface-secondary"
                          aria-label="Edit"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => setDeleteConfirm(f.id)}
                          className="rounded-lg p-2 text-text-tertiary hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20"
                          aria-label="Delete"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add/Edit Modal */}
      <Modal
        open={modalOpen}
        onClose={() => {
          setModalOpen(false);
          resetForm();
        }}
        title={editingId ? 'Edit Custom Field' : 'Add Custom Field'}
        size="sm"
        footer={
          <div className="flex gap-3">
            <Button
              variant="secondary"
              onClick={() => {
                setModalOpen(false);
                resetForm();
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleSave} loading={saving} disabled={!form.name.trim()}>
              {editingId ? 'Save Changes' : 'Create Field'}
            </Button>
          </div>
        }
      >
        <FieldForm data={form} onChange={setForm} />
      </Modal>

      {/* Delete Confirm Modal */}
      <Modal
        open={deleteConfirm !== null}
        onClose={() => setDeleteConfirm(null)}
        title="Delete Custom Field"
        size="sm"
        footer={
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setDeleteConfirm(null)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={() => deleteConfirm && handleDelete(deleteConfirm)}
              loading={deleteField.isPending}
            >
              Delete
            </Button>
          </div>
        }
      >
        <p className="text-sm text-text-secondary dark:text-dark-text-secondary">
          This will remove the field definition. Existing data on contacts, deals, or accounts
          will remain in the database but won't be displayed as a custom field.
        </p>
      </Modal>
    </div>
  );
}
