import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Plus, UserPlus, AlertCircle, RefreshCw, Download } from 'lucide-react';
import { Input } from '../../components/atoms/input';
import { Button } from '../../components/atoms/button';
import { Card } from '../../components/molecules/card';
import { Badge } from '../../components/atoms/badge';
import { Avatar } from '../../components/atoms/avatar';
import { Skeleton } from '../../components/atoms/skeleton';
import { ExportButton } from '../../components/ui/export-button';
import { Table, type Column } from '../../components/ui/table';
import { cn } from '../../lib/utils';
import { useContacts } from '../../api/contacts';
import type { Contact } from '../../types';

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-surface-secondary dark:bg-dark-surface-secondary">
        <UserPlus className="h-8 w-8 text-text-tertiary dark:text-dark-text-tertiary" />
      </div>
      <h3 className="text-lg font-semibold text-text-primary dark:text-dark-text-primary">
        {message}
      </h3>
      <p className="mt-1 text-sm text-text-tertiary dark:text-dark-text-tertiary">
        Get started by adding your first contact.
      </p>
      <Button className="mt-4" variant="primary" icon={<Plus className="h-4 w-4" />}>
        Add Contact
      </Button>
    </div>
  );
}

function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-50 dark:bg-red-900/20">
        <AlertCircle className="h-8 w-8 text-red-500" />
      </div>
      <h3 className="text-lg font-semibold text-text-primary dark:text-dark-text-primary">
        {message}
      </h3>
      <p className="mt-1 text-sm text-text-tertiary dark:text-dark-text-tertiary">
        Please try again or contact support.
      </p>
      {onRetry && (
        <Button
          className="mt-4"
          variant="secondary"
          icon={<RefreshCw className="h-4 w-4" />}
          onClick={onRetry}
        >
          Try Again
        </Button>
      )}
    </div>
  );
}

export function ContactListPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const params: Record<string, string> = {
    page: String(page),
    page_size: String(pageSize),
  };
  if (search.trim()) {
    params.search = search.trim();
  }

  const { data, isLoading, isError, refetch } = useContacts(params);

  const contacts = data?.results ?? [];
  const totalCount = data?.count ?? 0;
  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));

  const handleSearch = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setSearch(e.target.value);
      setPage(1);
    },
    [],
  );

  const handleRowClick = useCallback(
    (contact: Contact) => {
      navigate(`/contacts/${contact.id}`);
    },
    [navigate],
  );

  const columns: Column<Contact>[] = [
    {
      header: 'Name',
      accessor: 'full_name',
      cell: (contact) => (
        <div className="flex items-center gap-3">
          <Avatar
            src={contact.avatar_url || undefined}
            fallback={`${contact.first_name} ${contact.last_name}`}
            size="sm"
          />
          <span className="font-medium text-text-primary dark:text-dark-text-primary">
            {contact.full_name}
          </span>
        </div>
      ),
    },
    {
      header: 'Email',
      accessor: 'email',
      cell: (contact) => (
        <span className="text-text-secondary dark:text-dark-text-secondary">
          {contact.email}
        </span>
      ),
    },
    {
      header: 'Phone',
      accessor: (contact) => contact.phone || contact.mobile || '-',
      cell: (contact) => (
        <span className="text-text-secondary dark:text-dark-text-secondary">
          {contact.phone || contact.mobile || '-'}
        </span>
      ),
    },
    {
      header: 'Job Title',
      accessor: (contact) => contact.job_title || '-',
      cell: (contact) => (
        <span className="text-text-secondary dark:text-dark-text-secondary">
          {contact.job_title || '-'}
        </span>
      ),
    },
    {
      header: 'Account',
      accessor: (contact) => contact.account_name || '-',
      cell: (contact) =>
        contact.account_name ? (
          <Badge variant="neutral" size="sm">
            {contact.account_name}
          </Badge>
        ) : (
          <span className="text-text-tertiary dark:text-dark-text-tertiary">-</span>
        ),
    },
    {
      header: 'Created',
      accessor: (contact) => formatDate(contact.created_at),
      cell: (contact) => (
        <span className="text-text-tertiary dark:text-dark-text-tertiary">
          {formatDate(contact.created_at)}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary dark:text-dark-text-primary">
            Contacts
          </h1>
          <p className="mt-1 text-sm text-text-secondary dark:text-dark-text-secondary">
            Manage your contacts and relationships.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ExportButton url="/contacts/export/csv/" filename="contacts.csv" label="Export CSV" variant="secondary" size="sm" />
          <Button icon={<Plus className="h-4 w-4" />}>Add Contact</Button>
        </div>
      </div>

      {/* Search */}
      <div className="max-w-md">
        <Input
          placeholder="Search contacts..."
          iconLeft={<Search className="h-4 w-4" />}
          value={search}
          onChange={handleSearch}
          aria-label="Search contacts"
        />
      </div>

      {/* Table */}
      {isError ? (
        <Card>
          <ErrorState message="Failed to load contacts" onRetry={() => refetch()} />
        </Card>
      ) : contacts.length === 0 && !isLoading ? (
        <Card>
          <EmptyState message="No contacts yet" />
        </Card>
      ) : (
        <Card className="overflow-hidden p-0">
          <Table<Contact>
            columns={columns}
            data={contacts}
            loading={isLoading}
            skeletonRows={8}
            onRowClick={handleRowClick}
            emptyContent="No contacts found."
          />

          {/* Pagination */}
          {!isLoading && totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-border px-4 py-3 dark:border-dark-border">
              <p className="text-sm text-text-secondary dark:text-dark-text-secondary">
                Showing{' '}
                <span className="font-medium">
                  {Math.min((page - 1) * pageSize + 1, totalCount)}
                </span>{' '}
                to{' '}
                <span className="font-medium">
                  {Math.min(page * pageSize, totalCount)}
                </span>{' '}
                of <span className="font-medium">{totalCount}</span> contacts
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </Button>
                <div className="flex items-center gap-1">
                  {generatePageNumbers(page, totalPages).map((p, i) =>
                    p === '...' ? (
                      <span
                        key={`ellipsis-${i}`}
                        className="px-1 text-sm text-text-tertiary dark:text-dark-text-tertiary"
                      >
                        ...
                      </span>
                    ) : (
                      <button
                        key={p}
                        type="button"
                        onClick={() => setPage(p as number)}
                        className={cn(
                          'flex h-8 w-8 items-center justify-center rounded-md text-sm transition-colors',
                          p === page
                            ? 'bg-brand-600 text-white'
                            : 'text-text-secondary hover:bg-surface-secondary dark:text-dark-text-secondary dark:hover:bg-dark-surface-secondary',
                        )}
                      >
                        {p}
                      </button>
                    ),
                  )}
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

function generatePageNumbers(
  current: number,
  total: number,
): (number | '...')[] {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }

  const pages: (number | '...')[] = [1];

  if (current > 3) {
    pages.push('...');
  }

  const start = Math.max(2, current - 1);
  const end = Math.min(total - 1, current + 1);

  for (let i = start; i <= end; i++) {
    pages.push(i);
  }

  if (current < total - 2) {
    pages.push('...');
  }

  pages.push(total);

  return pages;
}