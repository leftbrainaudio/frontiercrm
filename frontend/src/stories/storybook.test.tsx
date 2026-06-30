/**
 * Storybook Component Tests
 *
 * Tests all Storybook components for:
 * 1. Render without error (light mode)
 * 2. Render without error (dark mode)
 * 3. Basic accessibility checks
 *
 * Each component is rendered as it would be in Storybook,
 * using the same decorators (Router, QueryClient, DndContext).
 */

import { render, screen, within } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DndContext, closestCorners } from '@dnd-kit/core';
import { Button } from '../components/atoms/button';
import { Input } from '../components/atoms/input';
import { Badge } from '../components/atoms/badge';
import { Avatar } from '../components/atoms/avatar';
import { Tag } from '../components/atoms/tag';
import { Select } from '../components/atoms/select';
import { IconButton } from '../components/atoms/icon-button';
import { Spinner } from '../components/ui/spinner';
import { Skeleton } from '../components/atoms/skeleton';
import { Tabs } from '../components/ui/tabs';
import { Pagination } from '../components/ui/pagination';
import { Tooltip } from '../components/ui/tooltip';
import { Modal } from '../components/molecules/modal';
import { MetricCard } from '../components/molecules/metric-card';
import { DealCard } from '../components/molecules/deal-card';
import { PageHeader } from '../components/molecules/page-header';
import { SearchInput } from '../components/molecules/search-input';
import { Dropdown } from '../components/molecules/dropdown';
import { Table } from '../components/ui/table';
import { StatCard } from '../components/molecules/stat-card';
import { Sidebar } from '../components/organisms/sidebar';
import { TopBar } from '../components/organisms/topbar';
import { Card } from '../components/molecules/card';
import { AppLayout } from '../components/templates/app-layout';

// ── Helpers ──────────────────────────────────────────────────────────────────

function createQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } });
}

function withProviders(ui: React.ReactElement) {
  const queryClient = createQueryClient();
  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        {ui}
      </QueryClientProvider>
    </BrowserRouter>
  );
}

function enableDarkMode() {
  document.documentElement.classList.add('dark');
}

function disableDarkMode() {
  document.documentElement.classList.remove('dark');
}

function expectDarkClassPresent() {
  expect(document.documentElement.classList.contains('dark')).toBe(true);
}

// ── Atoms ────────────────────────────────────────────────────────────────────

describe('Atoms — Storybook components', () => {
  beforeEach(() => disableDarkMode());
  afterEach(() => disableDarkMode());

  describe('Button', () => {
    it('renders primary variant', () => {
      render(withProviders(<Button>Click me</Button>));
      expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
    });

    it('renders in dark mode', () => {
      enableDarkMode();
      render(withProviders(<Button variant="primary">Dark</Button>));
      expect(screen.getByRole('button', { name: 'Dark' })).toBeInTheDocument();
      expectDarkClassPresent();
    });

    it('renders all variants without error', () => {
      const variants = ['primary', 'secondary', 'outline', 'ghost', 'danger'] as const;
      for (const variant of variants) {
        const { unmount } = render(withProviders(<Button variant={variant}>{variant}</Button>));
        expect(screen.getByRole('button', { name: variant })).toBeInTheDocument();
        unmount();
      }
    });

    it('renders loading state', () => {
      render(withProviders(<Button loading>Saving</Button>));
      const btn = screen.getByRole('button', { name: 'Saving' });
      expect(btn).toBeDisabled();
      expect(btn).toHaveAttribute('aria-busy', 'true');
    });

    it('renders disabled state', () => {
      render(withProviders(<Button disabled>Disabled</Button>));
      expect(screen.getByRole('button', { name: 'Disabled' })).toBeDisabled();
    });

    it('renders full width', () => {
      const { container } = render(withProviders(<Button fullWidth>Full</Button>));
      expect(container.querySelector('button')?.className).toContain('w-full');
    });

    it('renders with icon', () => {
      render(withProviders(<Button icon={<span data-testid="icon" />}>With Icon</Button>));
      expect(screen.getByRole('button', { name: 'With Icon' })).toBeInTheDocument();
    });
  });

  describe('Input', () => {
    it('renders default state', () => {
      render(withProviders(<Input placeholder="Enter text..." />));
      expect(screen.getByPlaceholderText('Enter text...')).toBeInTheDocument();
    });

    it('renders with label and associates correctly', () => {
      render(withProviders(<Input label="Email" placeholder="you@example.com" />));
      const input = screen.getByLabelText('Email');
      expect(input).toBeInTheDocument();
      expect(input).toHaveAttribute('id', 'email');
    });

    it('renders with error message and aria-invalid', () => {
      render(withProviders(<Input label="Password" error="Password must be at least 8 characters" />));
      expect(screen.getByRole('alert')).toHaveTextContent('Password must be at least 8 characters');
      expect(screen.getByLabelText('Password')).toHaveAttribute('aria-invalid', 'true');
    });

    it('renders with helper text', () => {
      render(withProviders(<Input label="Username" helperText="This will be your display name" />));
      expect(screen.getByText('This will be your display name')).toBeInTheDocument();
    });

    it('renders disabled state', () => {
      render(withProviders(<Input label="Disabled" value="Cannot edit" disabled />));
      expect(screen.getByLabelText('Disabled')).toBeDisabled();
    });

    it('renders in dark mode', () => {
      enableDarkMode();
      render(withProviders(<Input placeholder="Dark input" />));
      expect(screen.getByPlaceholderText('Dark input')).toBeInTheDocument();
      expectDarkClassPresent();
    });

    it('renders with icons', () => {
      const { container } = render(withProviders(
        <Input iconLeft={<span data-testid="left-icon" />} iconRight={<span data-testid="right-icon" />} />
      ));
      expect(container.querySelector('input')).toBeInTheDocument();
    });
  });

  describe('Badge', () => {
    it('renders with text', () => {
      render(withProviders(<Badge>3</Badge>));
      expect(screen.getByText('3')).toBeInTheDocument();
    });
    it('renders all variants', () => {
      const variants = ['neutral', 'primary', 'success', 'warning', 'danger', 'info'] as const;
      for (const variant of variants) {
        const { unmount } = render(withProviders(<Badge variant={variant}>{variant}</Badge>));
        expect(screen.getByText(variant)).toBeInTheDocument();
        unmount();
      }
    });
    it('renders in dark mode', () => {
      enableDarkMode();
      render(withProviders(<Badge variant="neutral">Dark</Badge>));
      expect(screen.getByText('Dark')).toBeInTheDocument();
      expectDarkClassPresent();
    });
  });

  describe('Avatar', () => {
    it('renders with fallback initials', () => {
      render(withProviders(<Avatar fallback="John Doe" />));
      // Avatar computes initials "JD" from fallback "John Doe"
      const img = screen.getByRole('img');
      expect(img).toBeInTheDocument();
      expect(img).toHaveTextContent('JD');
    });
    it('renders with image', () => {
      render(withProviders(<Avatar src="https://example.com/photo.jpg" alt="User" />));
      const img = screen.getByAltText('User');
      expect(img).toBeInTheDocument();
      expect(img).toHaveAttribute('src', 'https://example.com/photo.jpg');
    });
    it('renders online indicator', () => {
      render(withProviders(<Avatar fallback="Online User" online />));
      expect(screen.getByRole('status', { name: 'Online' })).toBeInTheDocument();
    });
    it('renders in dark mode', () => {
      enableDarkMode();
      render(withProviders(<Avatar fallback="Dark Mode" />));
      expect(screen.getByRole('img')).toBeInTheDocument();
      expectDarkClassPresent();
    });
  });

  describe('Tag', () => {
    it('renders with text', () => {
      render(withProviders(<Tag>High Priority</Tag>));
      expect(screen.getByText('High Priority')).toBeInTheDocument();
    });
    it('renders removable tag', () => {
      render(withProviders(<Tag removable onRemove={() => {}}>Removable</Tag>));
      expect(screen.getByText('Removable')).toBeInTheDocument();
      expect(screen.getByRole('button')).toBeInTheDocument();
    });
    it('renders in dark mode', () => {
      enableDarkMode();
      render(withProviders(<Tag variant="primary">Dark</Tag>));
      expect(screen.getByText('Dark')).toBeInTheDocument();
      expectDarkClassPresent();
    });
  });

  describe('Select', () => {
    it('renders default state', () => {
      render(withProviders(<Select><option>Option 1</option></Select>));
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });
    it('renders with label', () => {
      render(withProviders(<Select label="Status"><option>Active</option></Select>));
      expect(screen.getByLabelText('Status')).toBeInTheDocument();
    });
    it('renders in dark mode', () => {
      enableDarkMode();
      render(withProviders(<Select label="Dark"><option>D</option></Select>));
      expect(screen.getByLabelText('Dark')).toBeInTheDocument();
      expectDarkClassPresent();
    });
  });

  describe('IconButton', () => {
    it('renders with accessible label', () => {
      render(withProviders(<IconButton icon={<span data-testid="icon" />} label="Close" />));
      expect(screen.getByRole('button', { name: 'Close' })).toBeInTheDocument();
    });
    it('renders in dark mode', () => {
      enableDarkMode();
      render(withProviders(<IconButton icon={<span />} label="Dark" />));
      expect(screen.getByRole('button', { name: 'Dark' })).toBeInTheDocument();
      expectDarkClassPresent();
    });
  });

  describe('Spinner', () => {
    it('renders with status role', () => {
      render(withProviders(<Spinner />));
      expect(screen.getByRole('status')).toBeInTheDocument();
    });
    it('renders with aria-label', () => {
      render(withProviders(<Spinner label="Loading data..." />));
      const spinner = screen.getByRole('status');
      expect(spinner).toHaveAttribute('aria-label', 'Loading data...');
    });
    it('renders fullPage mode with visible label', () => {
      render(withProviders(<Spinner label="Please wait" fullPage />));
      expect(screen.getByText('Please wait')).toBeInTheDocument();
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
    it('renders in dark mode', () => {
      enableDarkMode();
      render(withProviders(<Spinner />));
      expect(screen.getByRole('status')).toBeInTheDocument();
      expectDarkClassPresent();
    });
  });

  describe('Skeleton', () => {
    it('renders text skeleton', () => {
      const { container } = render(withProviders(<Skeleton variant="text" />));
      expect(container.querySelector('div')).toBeInTheDocument();
    });
    it('renders circular skeleton', () => {
      const { container } = render(withProviders(<Skeleton variant="circular" />));
      expect(container.querySelector('div')).toBeInTheDocument();
    });
    it('renders rectangular skeleton', () => {
      const { container } = render(withProviders(<Skeleton variant="rectangular" />));
      expect(container.querySelector('div')).toBeInTheDocument();
    });
    it('renders in dark mode', () => {
      enableDarkMode();
      const { container } = render(withProviders(<Skeleton variant="text" />));
      expect(container.querySelector('div')).toBeInTheDocument();
      expectDarkClassPresent();
    });
  });

  describe('Tabs', () => {
    it('renders tabs with panels using data-driven API', () => {
      render(withProviders(
        <Tabs
          tabs={[
            { label: 'Tab One', id: 'tab1' },
            { label: 'Tab Two', id: 'tab2' },
            { label: 'Disabled Tab', disabled: true, id: 'tab3' },
          ]}
        >
          {(activeIdx) => (
            <div>
              {activeIdx === 0 && <p>Panel One</p>}
              {activeIdx === 1 && <p>Panel Two</p>}
              {activeIdx === 2 && <p>Panel Three</p>}
            </div>
          )}
        </Tabs>
      ));
      const tablist = screen.getByRole('tablist');
      expect(tablist).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: 'Tab One' })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: 'Tab Two' })).toBeInTheDocument();
      expect(screen.getByText('Panel One')).toBeInTheDocument();
    });

    it('switches active tab', () => {
      render(withProviders(
        <Tabs
          tabs={[
            { label: 'First', id: 'f' },
            { label: 'Second', id: 's' },
          ]}
          defaultIndex={1}
        >
          {(i) => <p>Panel {i}</p>}
        </Tabs>
      ));
      expect(screen.getByText('Panel 1')).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: 'Second' })).toHaveAttribute('aria-selected', 'true');
    });

    it('renders disabled tab', () => {
      render(withProviders(
        <Tabs
          tabs={[
            { label: 'Active', id: 'a' },
            { label: 'Disabled', disabled: true, id: 'd' },
          ]}
        >
          {() => <p>content</p>}
        </Tabs>
      ));
      const disabledTab = screen.getByRole('tab', { name: 'Disabled' });
      expect(disabledTab).toBeDisabled();
      expect(disabledTab).toHaveAttribute('aria-disabled', 'true');
    });

    it('renders in dark mode', () => {
      enableDarkMode();
      render(withProviders(
        <Tabs tabs={[{ label: 'Dark Tab', id: 'dt' }]}>
          {() => <p>dark</p>}
        </Tabs>
      ));
      expect(screen.getByRole('tab', { name: 'Dark Tab' })).toBeInTheDocument();
      expectDarkClassPresent();
    });
  });

  describe('Pagination', () => {
    it('renders page buttons', () => {
      render(withProviders(<Pagination pageCount={5} currentPage={1} onChange={() => {}} />));
      expect(screen.getByLabelText('Page 1')).toBeInTheDocument();
      expect(screen.getByLabelText('Page 5')).toBeInTheDocument();
    });

    it('disables prev button on first page', () => {
      render(withProviders(<Pagination pageCount={5} currentPage={1} onChange={() => {}} />));
      expect(screen.getByRole('button', { name: /previous/i })).toBeDisabled();
    });

    it('disables next button on last page', () => {
      render(withProviders(<Pagination pageCount={5} currentPage={5} onChange={() => {}} />));
      expect(screen.getByRole('button', { name: /next/i })).toBeDisabled();
    });

    it('returns null when pageCount <= 1', () => {
      const { container } = render(withProviders(<Pagination pageCount={1} currentPage={1} onChange={() => {}} />));
      expect(container.innerHTML).toBe('');
    });

    it('renders in dark mode', () => {
      enableDarkMode();
      render(withProviders(<Pagination pageCount={3} currentPage={2} onChange={() => {}} />));
      expect(screen.getByLabelText('Page 2')).toBeInTheDocument();
      expectDarkClassPresent();
    });

    it('shows compact mode', () => {
      render(withProviders(<Pagination pageCount={10} currentPage={5} onChange={() => {}} compact />));
      // Compact mode shows fewer siblings
      const nav = screen.getByRole('navigation');
      expect(nav).toBeInTheDocument();
    });
  });

  describe('Tooltip', () => {
    it('renders trigger element', () => {
      render(withProviders(
        <Tooltip content="Tooltip content">
          <Button>Hover me</Button>
        </Tooltip>
      ));
      expect(screen.getByRole('button', { name: 'Hover me' })).toBeInTheDocument();
    });
    it('renders in dark mode', () => {
      enableDarkMode();
      render(withProviders(
        <Tooltip content="Dark tip">
          <Button>Dark</Button>
        </Tooltip>
      ));
      expect(screen.getByRole('button', { name: 'Dark' })).toBeInTheDocument();
      expectDarkClassPresent();
    });
  });

  // ── Modal ────────────────────────────────────────────────────────────────
  describe('Modal (molecule)', () => {
    it('renders when open', () => {
      render(withProviders(
        <Modal open onClose={() => {}} title="Test Modal">
          <p>Modal content</p>
        </Modal>
      ));
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
      expect(within(dialog).getByText('Test Modal')).toBeInTheDocument();
    });
    it('does not render when closed', () => {
      render(withProviders(
        <Modal open={false} onClose={() => {}} title="Hidden Modal">
          <p>Hidden content</p>
        </Modal>
      ));
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
    it('renders in dark mode', () => {
      enableDarkMode();
      render(withProviders(
        <Modal open onClose={() => {}} title="Dark Modal">
          <p>dark</p>
        </Modal>
      ));
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expectDarkClassPresent();
    });
  });

  // ── Molecules ────────────────────────────────────────────────────────────
  describe('MetricCard', () => {
    it('renders with value and label', () => {
      render(withProviders(<MetricCard label="Revenue" value="$50,000" />));
      expect(screen.getByText('Revenue')).toBeInTheDocument();
      expect(screen.getByText('$50,000')).toBeInTheDocument();
    });
    it('shows trend when provided (string)', () => {
      render(withProviders(<MetricCard label="Growth" value="12%" trend="+5%" trendUp />));
      expect(screen.getByText('+5%')).toBeInTheDocument();
    });
    it('shows negative trend styling', () => {
      render(withProviders(<MetricCard label="Churn" value="3%" trend="-1%" trendUp={false} />));
      expect(screen.getByText('-1%')).toBeInTheDocument();
    });
    it('renders loading state', () => {
      const { container } = render(withProviders(<MetricCard label="Loading" value="..." loading />));
      // Loading state shows skeleton, not the label
      expect(container.querySelector('.space-y-3')).toBeInTheDocument();
    });
    it('renders in dark mode', () => {
      enableDarkMode();
      render(withProviders(<MetricCard label="Dark" value="100%" />));
      expect(screen.getByText('Dark')).toBeInTheDocument();
      expectDarkClassPresent();
    });
  });

  describe('DealCard', () => {
    it('renders deal info from deal object', () => {
      render(withProviders(
        <DealCard deal={{
          id: '1',
          name: 'Enterprise Deal',
          value: 50000,
          contact_name: 'Alice Johnson',
          expected_close_date: '2026-08-15',
        }} />
      ));
      expect(screen.getByText('Enterprise Deal')).toBeInTheDocument();
      expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
    });
    it('renders with stage badge', () => {
      render(withProviders(
        <DealCard deal={{
          id: '2',
          name: 'Pro Deal',
          value: 12000,
          stage_name: 'Negotiation',
        }} />
      ));
      expect(screen.getByText('Negotiation')).toBeInTheDocument();
    });
    it('renders loading state', () => {
      const { container } = render(withProviders(<DealCard deal={{ id: '3', name: 'Loading', value: 0 }} loading />));
      expect(container.querySelector('.space-y-2')).toBeInTheDocument();
    });
    it('renders in dark mode', () => {
      enableDarkMode();
      render(withProviders(
        <DealCard deal={{ id: '4', name: 'Dark Deal', value: 999 }} />
      ));
      expect(screen.getByText('Dark Deal')).toBeInTheDocument();
      expectDarkClassPresent();
    });
  });

  describe('PageHeader', () => {
    it('renders title and description', () => {
      render(withProviders(<PageHeader title="Dashboard" description="Overview of your business" />));
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Overview of your business')).toBeInTheDocument();
    });
    it('renders actions slot', () => {
      render(withProviders(<PageHeader title="Deals" actions={<Button>Add Deal</Button>} />));
      expect(screen.getByRole('button', { name: 'Add Deal' })).toBeInTheDocument();
    });
    it('renders in dark mode', () => {
      enableDarkMode();
      render(withProviders(<PageHeader title="Dark Header" description="dark mode" />));
      expect(screen.getByText('Dark Header')).toBeInTheDocument();
      expectDarkClassPresent();
    });
  });

  describe('SearchInput', () => {
    it('renders with placeholder', () => {
      render(withProviders(<SearchInput placeholder="Search deals..." />));
      expect(screen.getByPlaceholderText('Search deals...')).toBeInTheDocument();
    });
    it('renders in dark mode', () => {
      enableDarkMode();
      render(withProviders(<SearchInput placeholder="Dark search" />));
      expect(screen.getByPlaceholderText('Dark search')).toBeInTheDocument();
      expectDarkClassPresent();
    });
  });

  describe('Dropdown', () => {
    it('renders trigger button', () => {
      render(withProviders(<Dropdown trigger={<Button>Actions</Button>} items={[{ label: 'Edit' }]} />));
      expect(screen.getByRole('button', { name: 'Actions' })).toBeInTheDocument();
    });
    it('renders with icons and dividers', () => {
      render(withProviders(
        <Dropdown
          trigger={<Button>More</Button>}
          items={[
            { label: 'Edit', icon: <span data-testid="edit-icon" /> },
            { label: '', divider: true },
            { label: 'Delete', danger: true },
          ]}
        />
      ));
      expect(screen.getByRole('button', { name: 'More' })).toBeInTheDocument();
    });
    it('renders in dark mode', () => {
      enableDarkMode();
      render(withProviders(<Dropdown trigger={<Button>Dark</Button>} items={[{ label: 'Option' }]} />));
      expect(screen.getByRole('button', { name: 'Dark' })).toBeInTheDocument();
      expectDarkClassPresent();
    });
  });

  describe('Table', () => {
    it('renders columns and data', () => {
      interface Deal { name: string; status: string; value: number }
      const columns = [
        { header: 'Name', accessor: 'name' as const },
        { header: 'Status', accessor: 'status' as const },
      ];
      const data: Deal[] = [
        { name: 'Deal A', status: 'Active', value: 1000 },
        { name: 'Deal B', status: 'Closed', value: 2000 },
      ];
      render(withProviders(<Table columns={columns} data={data} />));
      expect(screen.getByText('Name')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Deal A')).toBeInTheDocument();
      expect(screen.getByText('Deal B')).toBeInTheDocument();
    });
    it('renders empty state', () => {
      render(withProviders(<Table columns={[{ header: 'Name', accessor: 'name' as const }]} data={[]} />));
      expect(screen.getByText('No data available.')).toBeInTheDocument();
    });
    it('renders loading state', () => {
      const { container } = render(withProviders(
        <Table columns={[{ header: 'Name', accessor: 'name' as const }]} data={[]} loading />
      ));
      expect(container.querySelector('tbody')).toBeInTheDocument();
    });
    it('renders in dark mode', () => {
      enableDarkMode();
      render(withProviders(
        <Table columns={[{ header: 'Name', accessor: 'name' as const }]} data={[{ name: 'Dark' }]} />
      ));
      expect(screen.getByText('Dark')).toBeInTheDocument();
      expectDarkClassPresent();
    });
  });

  describe('StatCard', () => {
    it('renders stats via stats array', () => {
      render(withProviders(
        <StatCard
          title="Overview"
          stats={[
            { label: 'Total Value', value: '$150,000' },
            { label: 'Active Deals', value: 42 },
          ]}
        />
      ));
      expect(screen.getByText('Overview')).toBeInTheDocument();
      expect(screen.getByText('Total Value')).toBeInTheDocument();
      expect(screen.getByText('$150,000')).toBeInTheDocument();
      expect(screen.getByText('Active Deals')).toBeInTheDocument();
      expect(screen.getByText('42')).toBeInTheDocument();
    });
    it('renders with trend indicators', () => {
      render(withProviders(
        <StatCard
          stats={[
            { label: 'Growth', value: '12%', trend: '+5%', trendUp: true },
            { label: 'Churn', value: '3%', trend: '-1%', trendUp: false },
          ]}
        />
      ));
      expect(screen.getByText('+5%')).toBeInTheDocument();
      expect(screen.getByText('-1%')).toBeInTheDocument();
    });
    it('renders loading state', () => {
      const { container } = render(withProviders(
        <StatCard title="Loading" stats={[]} loading columns={2} />
      ));
      expect(container.querySelector('.space-y-2')).toBeInTheDocument();
    });
    it('renders in dark mode', () => {
      enableDarkMode();
      render(withProviders(
        <StatCard stats={[{ label: 'Dark Stat', value: '100%' }]} />
      ));
      expect(screen.getByText('Dark Stat')).toBeInTheDocument();
      expectDarkClassPresent();
    });
  });

  // ── Organisms ────────────────────────────────────────────────────────────
  describe('Sidebar', () => {
    it('renders in expanded state', () => {
      render(withProviders(<Sidebar collapsed={false} mobileOpen={false} onToggle={() => {}} onMobileClose={() => {}} />));
      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });
    it('renders in collapsed state', () => {
      const { container } = render(withProviders(<Sidebar collapsed mobileOpen={false} onToggle={() => {}} onMobileClose={() => {}} />));
      expect(container.querySelector('nav')).toBeInTheDocument();
    });
    it('renders in dark mode', () => {
      enableDarkMode();
      render(withProviders(<Sidebar collapsed={false} mobileOpen={false} onToggle={() => {}} onMobileClose={() => {}} />));
      expect(screen.getByRole('navigation')).toBeInTheDocument();
      expectDarkClassPresent();
    });
  });

  describe('TopBar', () => {
    it('renders banner landmark', () => {
      render(withProviders(<TopBar />));
      expect(screen.getByRole('banner')).toBeInTheDocument();
    });
    it('renders in dark mode', () => {
      enableDarkMode();
      render(withProviders(<TopBar />));
      expect(screen.getByRole('banner')).toBeInTheDocument();
      expectDarkClassPresent();
    });
  });

  describe('Card', () => {
    it('renders children', () => {
      render(withProviders(<Card><p>Card content</p></Card>));
      expect(screen.getByText('Card content')).toBeInTheDocument();
    });
    it('renders interactive variant', () => {
      const { container } = render(withProviders(<Card variant="interactive"><p>Interactive</p></Card>));
      expect(screen.getByText('Interactive')).toBeInTheDocument();
    });
    it('renders in dark mode', () => {
      enableDarkMode();
      render(withProviders(<Card><p>Dark card</p></Card>));
      expect(screen.getByText('Dark card')).toBeInTheDocument();
      expectDarkClassPresent();
    });
  });

  // ── Templates ────────────────────────────────────────────────────────────
  describe('AppLayout', () => {
    it('renders loading state when auth is loading', () => {
      render(withProviders(<AppLayout />));
      // AppLayout shows a loading spinner until auth resolves
      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText('Loading')).toBeInTheDocument();
    });
    it('renders in dark mode loading state', () => {
      enableDarkMode();
      render(withProviders(<AppLayout />));
      expect(screen.getByText('Loading')).toBeInTheDocument();
      expectDarkClassPresent();
    });
  });
});
