import {
  useMemo,
  useState,
  type ReactNode,
  type HTMLAttributes,
  type KeyboardEvent,
} from 'react';
import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react';
import { cn } from '../../lib/utils';
import { Skeleton } from '../atoms/skeleton';

export interface Column<T> {
  /** Column header text */
  header: string;
  /** Accessor key or function to get cell value */
  accessor: keyof T | ((row: T) => ReactNode);
  /** Whether the column is sortable */
  sortable?: boolean;
  /** Custom cell renderer (receives the row data) */
  cell?: (row: T) => ReactNode;
  /** Optional className for header */
  headerClassName?: string;
  /** Optional className for cells */
  cellClassName?: string;
  /** Column width (Tailwind class) */
  width?: string;
}

export interface TableProps<T> extends HTMLAttributes<HTMLDivElement> {
  /** Column definitions */
  columns: Column<T>[];
  /** Row data */
  data: T[];
  /** Loading state — renders skeleton rows */
  loading?: boolean;
  /** Number of skeleton rows when loading */
  skeletonRows?: number;
  /** Click handler for rows */
  onRowClick?: (row: T) => void;
  /** Show striped rows */
  striped?: boolean;
  /** Show borders between rows */
  bordered?: boolean;
  /** Enable row selection via checkboxes */
  selectable?: boolean;
  /** Controlled selected row keys (requires rowKey) */
  selectedKeys?: Set<string>;
  /** Selection change handler */
  onSelectionChange?: (selectedKeys: Set<string>) => void;
  /** Row key extractor (required for selection) */
  rowKey?: (row: T) => string;
  /** Empty state content */
  emptyContent?: ReactNode;
  /** Controlled sort column key */
  sortColumn?: string;
  /** Controlled sort direction */
  sortDirection?: 'asc' | 'desc';
  /** Sort change handler */
  onSort?: (column: string, direction: 'asc' | 'desc') => void;
}

export function Table<T>({
  columns,
  data,
  loading = false,
  skeletonRows = 5,
  onRowClick,
  striped = false,
  bordered = false,
  selectable = false,
  selectedKeys,
  onSelectionChange,
  rowKey,
  emptyContent = 'No data available.',
  sortColumn: controlledSortColumn,
  sortDirection: controlledSortDirection,
  onSort,
  className,
  ...props
}: TableProps<T>) {
  const [internalSortColumn, setInternalSortColumn] = useState<string | undefined>();
  const [internalSortDirection, setInternalSortDirection] = useState<'asc' | 'desc'>('asc');

  const isControlled = controlledSortColumn !== undefined;
  const activeSortColumn = isControlled ? controlledSortColumn : internalSortColumn;
  const activeSortDirection = isControlled ? controlledSortDirection : internalSortDirection;

  const sortedData = useMemo(() => {
    if (!activeSortColumn || loading) return data;

    const col = columns.find((c) => c.header === activeSortColumn);
    if (!col || !col.sortable) return data;

    return [...data].sort((a, b) => {
      const aVal =
        typeof col.accessor === 'function'
          ? (col.accessor(a) ?? '')
          : (a[col.accessor] ?? '');
      const bVal =
        typeof col.accessor === 'function'
          ? (col.accessor(b) ?? '')
          : (b[col.accessor] ?? '');

      const cmp = String(aVal).localeCompare(String(bVal), undefined, { numeric: true });
      return activeSortDirection === 'asc' ? cmp : -cmp;
    });
  }, [data, activeSortColumn, activeSortDirection, columns, loading]);

  const handleSort = (column: string) => {
    if (onSort) {
      const newDir =
        activeSortColumn === column && activeSortDirection === 'asc' ? 'desc' : 'asc';
      onSort(column, newDir);
    } else {
      setInternalSortColumn((prev) => {
        if (prev !== column) {
          setInternalSortDirection('asc');
          return column;
        }
        return column;
      });
      setInternalSortDirection((prev) => (activeSortColumn === column && prev === 'asc' ? 'desc' : 'asc'));
    }
  };

  const getCellValue = (row: T, col: Column<T>): ReactNode => {
    if (col.cell) return col.cell(row);
    if (typeof col.accessor === 'function') return col.accessor(row);
    return (row[col.accessor] as ReactNode) ?? null;
  };

  const allSelected =
    selectable &&
    data.length > 0 &&
    selectedKeys &&
    rowKey &&
    data.every((row) => selectedKeys.has(rowKey(row)));

  const handleSelectAll = () => {
    if (!onSelectionChange || !rowKey) return;
    if (allSelected) {
      onSelectionChange(new Set());
    } else {
      onSelectionChange(new Set(data.map(rowKey)));
    }
  };

  const handleRowSelect = (row: T) => {
    if (!onSelectionChange || !rowKey || !selectedKeys) return;
    const key = rowKey(row);
    const next = new Set(selectedKeys);
    if (next.has(key)) {
      next.delete(key);
    } else {
      next.add(key);
    }
    onSelectionChange(next);
  };

  const handleRowKeyDown = (e: KeyboardEvent, row: T) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onRowClick?.(row);
    }
  };

  const renderSkeletonRow = (rowIndex: number) => (
    <tr key={`skeleton-${rowIndex}`}>
      {selectable && (
        <td className="px-4 py-2.5">
          <Skeleton variant="rectangular" width={16} height={16} />
        </td>
      )}
      {columns.map((col, ci) => (
        <td
          key={ci}
          className={cn('px-4 py-2.5', col.cellClassName)}
          style={{ width: col.width }}
        >
          <Skeleton variant="text" width={`${60 + Math.random() * 30}%`} />
        </td>
      ))}
    </tr>
  );

  return (
    <div className={cn('w-full overflow-x-auto rounded-lg border border-border dark:border-dark-border', className)} {...props}>
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-border bg-surface-secondary dark:border-dark-border dark:bg-dark-surface-secondary">
            {selectable && (
              <th className="w-10 px-4 py-3">
                <input
                  type="checkbox"
                  checked={!!allSelected}
                  onChange={handleSelectAll}
                  className="h-4 w-4 rounded border-border text-brand-600 focus:ring-brand-500 dark:border-dark-border"
                  aria-label="Select all rows"
                />
              </th>
            )}
            {columns.map((col) => (
              <th
                key={col.header}
                className={cn(
                  'px-4 py-3 text-xs font-semibold uppercase tracking-wider text-text-secondary dark:text-dark-text-secondary',
                  col.sortable && 'cursor-pointer select-none hover:text-text-primary dark:hover:text-dark-text-primary',
                  col.headerClassName,
                )}
                style={{ width: col.width }}
                onClick={() => col.sortable && handleSort(col.header)}
                aria-sort={
                  activeSortColumn === col.header
                    ? activeSortDirection === 'asc'
                      ? 'ascending'
                      : 'descending'
                    : undefined
                }
              >
                <div className="inline-flex items-center gap-1">
                  {col.header}
                  {col.sortable && (
                    <span className="shrink-0">
                      {activeSortColumn === col.header ? (
                        activeSortDirection === 'asc' ? (
                          <ChevronUp className="h-3.5 w-3.5" />
                        ) : (
                          <ChevronDown className="h-3.5 w-3.5" />
                        )
                      ) : (
                        <ChevronsUpDown className="h-3.5 w-3.5 text-text-tertiary dark:text-dark-text-tertiary" />
                      )}
                    </span>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border dark:divide-dark-border">
          {loading
            ? Array.from({ length: skeletonRows }).map((_, i) => renderSkeletonRow(i))
            : sortedData.length === 0
              ? (
                <tr>
                  <td
                    colSpan={columns.length + (selectable ? 1 : 0)}
                    className="px-4 py-12 text-center text-text-tertiary dark:text-dark-text-tertiary"
                  >
                    {emptyContent}
                  </td>
                </tr>
              )
              : sortedData.map((row, ri) => (
                <tr
                  key={rowKey ? rowKey(row) : ri}
                  className={cn(
                    'transition-colors',
                    onRowClick && 'cursor-pointer hover:bg-surface-tertiary dark:hover:bg-dark-surface-tertiary',
                    striped && ri % 2 === 1 && 'bg-surface-secondary/50 dark:bg-dark-surface-secondary/30',
                    bordered && 'border-b border-border dark:border-dark-border',
                    selectable && selectedKeys?.has(rowKey?.(row) ?? '') && 'bg-brand-50 dark:bg-brand-900/20 border-l-3 border-l-brand-500',
                  )}
                  onClick={() => {
                    onRowClick?.(row);
                  }}
                  onKeyDown={(e) => handleRowKeyDown(e, row)}
                  tabIndex={onRowClick ? 0 : undefined}
                  role={onRowClick ? 'button' : undefined}
                  aria-selected={selectable ? selectedKeys?.has(rowKey?.(row) ?? '') : undefined}
                >
                  {selectable && (
                    <td className="px-4 py-2.5">
                      <input
                        type="checkbox"
                        checked={selectedKeys?.has(rowKey?.(row) ?? '') ?? false}
                        onChange={() => handleRowSelect(row)}
                        className="h-4 w-4 rounded border-border text-brand-600 focus:ring-brand-500 dark:border-dark-border"
                        aria-label={`Select row ${ri + 1}`}
                      />
                    </td>
                  )}
                  {columns.map((col) => (
                    <td
                      key={col.header}
                      className={cn('px-4 py-2.5 text-text-primary dark:text-dark-text-primary', col.cellClassName)}
                    >
                      {getCellValue(row, col)}
                    </td>
                  ))}
                </tr>
              ))}
        </tbody>
      </table>
    </div>
  );
}