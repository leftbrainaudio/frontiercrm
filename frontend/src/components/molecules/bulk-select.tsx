import { useState, useCallback, useMemo, type ReactNode } from 'react';
import { cn } from '../../lib/utils';

export interface BulkSelectRenderProps<T> {
  selectedIds: Set<string>;
  isAllSelected: boolean;
  isIndeterminate: boolean;
  toggleOne: (id: string) => void;
  toggleAll: () => void;
  clearSelection: () => void;
  checkboxProps: (id: string) => {
    checked: boolean;
    onChange: () => void;
    'aria-label': string;
  };
  allCheckboxProps: {
    checked: boolean;
    indeterminate: boolean;
    onChange: () => void;
    'aria-label': string;
  };
  /** Total items on the current page */
  pageCount: number;
  /** Whether all items on the current page are selected */
  allPageSelected: boolean;
}

export interface BulkSelectProps<T> {
  items: T[];
  itemId: (item: T) => string;
  disabled?: boolean;
  /** Optional external selected set (controlled) */
  selectedIds?: Set<string>;
  onSelectionChange?: (ids: Set<string>) => void;
  children: (renderProps: BulkSelectRenderProps<T>) => ReactNode;
  /** Optional className for wrapping div */
  className?: string;
}

export function BulkSelect<T>({
  items,
  itemId,
  disabled = false,
  selectedIds: externalSelectedIds,
  onSelectionChange,
  children,
  className,
}: BulkSelectProps<T>) {
  const [internalSelectedIds, setInternalSelectedIds] = useState<Set<string>>(new Set());
  const isControlled = externalSelectedIds !== undefined;
  const selectedIds = isControlled ? externalSelectedIds : internalSelectedIds;

  const setSelectedIds = useCallback(
    (ids: Set<string>) => {
      if (!isControlled) setInternalSelectedIds(ids);
      onSelectionChange?.(ids);
    },
    [isControlled, onSelectionChange],
  );

  const currentPageIds = useMemo(() => items.map(itemId), [items, itemId]);

  const allPageSelected = useMemo(
    () =>
      currentPageIds.length > 0 &&
      currentPageIds.every((id) => selectedIds.has(id)),
    [currentPageIds, selectedIds],
  );

  const somePageSelected = useMemo(
    () => currentPageIds.some((id) => selectedIds.has(id)),
    [currentPageIds, selectedIds],
  );

  const isAllSelected = allPageSelected;
  const isIndeterminate = somePageSelected && !allPageSelected;

  const toggleOne = useCallback(
    (id: string) => {
      if (disabled) return;
      const next = new Set(selectedIds);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      setSelectedIds(next);
    },
    [selectedIds, setSelectedIds, disabled],
  );

  const toggleAll = useCallback(() => {
    if (disabled) return;
    if (allPageSelected) {
      const next = new Set(selectedIds);
      for (const id of currentPageIds) {
        next.delete(id);
      }
      setSelectedIds(next);
    } else {
      const next = new Set(selectedIds);
      for (const id of currentPageIds) {
        next.add(id);
      }
      setSelectedIds(next);
    }
  }, [disabled, allPageSelected, currentPageIds, selectedIds, setSelectedIds]);

  const clearSelection = useCallback(() => {
    if (disabled) return;
    setSelectedIds(new Set());
  }, [disabled, setSelectedIds]);

  const checkboxProps = useCallback(
    (id: string) => ({
      checked: selectedIds.has(id),
      onChange: () => toggleOne(id),
      'aria-label': 'Select row' as const,
    }),
    [selectedIds, toggleOne],
  );

  const allCheckboxProps = useMemo(
    () => ({
      checked: isAllSelected,
      indeterminate: isIndeterminate,
      onChange: toggleAll,
      'aria-label': 'Select all rows' as const,
    }),
    [isAllSelected, isIndeterminate, toggleAll],
  );

  return (
    <div className={cn(className)}>
      {children({
        selectedIds,
        isAllSelected,
        isIndeterminate,
        toggleOne,
        toggleAll,
        clearSelection,
        checkboxProps,
        allCheckboxProps,
        pageCount: currentPageIds.length,
        allPageSelected,
      })}
    </div>
  );
}