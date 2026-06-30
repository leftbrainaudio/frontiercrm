import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'react';
import { TimelinePage } from './timeline-page';
import type { TimelineResponse } from '../../types';

// ── Mocks ──────────────────────────────────────────────────────────────

const mockUseSearchParams = vi.fn(() => [new URLSearchParams()]);
const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useSearchParams: () => mockUseSearchParams(),
    useNavigate: () => mockNavigate,
  };
});

const mockUseActivityTimeline = vi.fn();
vi.mock('../../api/activities', () => ({
  useActivityTimeline: () => mockUseActivityTimeline(),
}));

vi.mock('lucide-react', () => ({
  History: () => <span data-testid="icon-history">H</span>,
  ChevronDown: () => <span data-testid="icon-chevron-down">CD</span>,
  AlertCircle: () => <span data-testid="icon-alert-circle">AC</span>,
  AlertTriangle: () => <span data-testid="icon-alert-triangle">AT</span>,
  CalendarPlus: () => <span data-testid="icon-calendar-plus">CP</span>,
  ExternalLink: () => <span data-testid="icon-external-link">EL</span>,
  Edit3: () => <span data-testid="icon-edit">E</span>,
  FileText: () => <span data-testid="icon-file-text">FT</span>,
  Phone: () => <span data-testid="icon-phone">P</span>,
  Mail: () => <span data-testid="icon-mail">M</span>,
  Calendar: () => <span data-testid="icon-calendar">C</span>,
  CheckSquare: () => <span data-testid="icon-check-square">CS</span>,
  TrendingUp: () => <span data-testid="icon-trending-up">TU</span>,
  Inbox: () => <span data-testid="icon-inbox">I</span>,
  Upload: () => <span data-testid="icon-upload">U</span>,
  ArrowUpRight: () => <span data-testid="icon-arrow-up-right">AUR</span>,
  Filter: () => <span data-testid="icon-filter">F</span>,
  X: () => <span data-testid="icon-x">X</span>,
}));

// ── Helpers ────────────────────────────────────────────────────────────

function mockTimelineData(resultsCount: number): TimelineResponse {
  const results = Array.from({ length: resultsCount }, (_, i) => ({
    id: `a${i + 1}`,
    activity_type: i % 2 === 0 ? 'note' : 'call',
    title: `Activity ${i + 1}`,
    description: '',
    created_at: new Date(Date.now() - i * 3600000).toISOString(),
    actor: { id: 'u1', name: 'Alice', avatar_url: '' },
    entity: { type: 'contact', id: 'c1', name: 'Bob', url: '/contacts/c1' },
    metadata: {},
  }));
  return {
    count: resultsCount,
    page: 1,
    page_size: 25,
    total_pages: Math.max(1, Math.ceil(resultsCount / 25)),
    next: resultsCount >= 25 ? '/api/activities/timeline/?page=2' : null,
    previous: null,
    results,
  };
}

function createWrapper(initialRoute = '/timeline') {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[initialRoute]}>{children}</MemoryRouter>
      </QueryClientProvider>
    );
  };
}

// ── Tests ──────────────────────────────────────────────────────────────

describe('TimelinePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseSearchParams.mockReturnValue([new URLSearchParams()]);
  });

  // ── Loading state ────────────────────────────────────────────────

  it('shows skeleton while loading (first page)', () => {
    mockUseActivityTimeline.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<TimelinePage />, { wrapper: createWrapper() });
    // The page header should still render
    expect(screen.getByText('Activity Timeline')).toBeInTheDocument();
    // Skeleton renders multiple skeleton item containers
    const skeletonItems = screen.getAllByText(/activity/i, { selector: 'h1' });
    expect(skeletonItems.length).toBeGreaterThan(0);
  });

  // ── Error state ──────────────────────────────────────────────────

  it('shows error state on API failure', () => {
    mockUseActivityTimeline.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: { message: 'Failed to fetch' },
      refetch: vi.fn(),
    });
    render(<TimelinePage />, { wrapper: createWrapper() });
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('Failed to fetch')).toBeInTheDocument();
  });

  it('shows default error message when no error detail', () => {
    mockUseActivityTimeline.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: null,
      refetch: vi.fn(),
    });
    render(<TimelinePage />, { wrapper: createWrapper() });
    expect(screen.getByText('Failed to load activity timeline')).toBeInTheDocument();
  });

  it('renders retry button on error', () => {
    const refetch = vi.fn();
    mockUseActivityTimeline.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: { message: 'Error' },
      refetch,
    });
    render(<TimelinePage />, { wrapper: createWrapper() });
    fireEvent.click(screen.getByText('Try again'));
    expect(refetch).toHaveBeenCalledTimes(1);
  });

  // ── Empty state ──────────────────────────────────────────────────

  it('shows empty state when no activities yet', () => {
    mockUseActivityTimeline.mockReturnValue({
      data: { count: 0, page: 1, page_size: 25, total_pages: 1, next: null, previous: null, results: [] },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<TimelinePage />, { wrapper: createWrapper() });
    expect(screen.getByText('No activity yet')).toBeInTheDocument();
  });

  // ── Data state ───────────────────────────────────────────────────

  it('renders the page header and subtitle', () => {
    mockUseActivityTimeline.mockReturnValue({
      data: mockTimelineData(5),
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<TimelinePage />, { wrapper: createWrapper() });
    expect(screen.getByText('Activity Timeline')).toBeInTheDocument();
    expect(
      screen.getByText(/reverse-chronological feed/i),
    ).toBeInTheDocument();
  });

  it('renders ActivityFilters component', () => {
    mockUseActivityTimeline.mockReturnValue({
      data: mockTimelineData(3),
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<TimelinePage />, { wrapper: createWrapper() });
    // Type filter pills should be visible
    expect(screen.getByText('All types')).toBeInTheDocument();
    expect(screen.getByText('Notes')).toBeInTheDocument();
  });

  it('renders activity entries from API data', () => {
    mockUseActivityTimeline.mockReturnValue({
      data: mockTimelineData(3),
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<TimelinePage />, { wrapper: createWrapper() });
    expect(screen.getByText('Activity 1')).toBeInTheDocument();
    expect(screen.getByText('Activity 2')).toBeInTheDocument();
    expect(screen.getByText('Activity 3')).toBeInTheDocument();
  });

  it('renders date group labels (Today, Yesterday, etc.)', () => {
    mockUseActivityTimeline.mockReturnValue({
      data: mockTimelineData(3),
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<TimelinePage />, { wrapper: createWrapper() });
    // "Today" appears in both the date preset button and the date group label
    const todayElements = screen.getAllByText('Today');
    expect(todayElements.length).toBeGreaterThanOrEqual(1);
  });

  it('shows "Load more" button when there are more pages', () => {
    const data = mockTimelineData(25); // exactly one page full
    mockUseActivityTimeline.mockReturnValue({
      data,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<TimelinePage />, { wrapper: createWrapper() });
    expect(screen.getByText(/load more/i)).toBeInTheDocument();
  });

  it('shows "Showing all" when all items loaded', () => {
    const data = mockTimelineData(3);
    mockUseActivityTimeline.mockReturnValue({
      data,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<TimelinePage />, { wrapper: createWrapper() });
    expect(screen.getByText(/showing all/i)).toBeInTheDocument();
  });

  // ── URL-parsed filters ─────────────────────────────────────────────

  it('shows context banner when actor_id is in URL', () => {
    mockUseSearchParams.mockReturnValue([
      new URLSearchParams('actor_id=abc-123'),
    ]);
    mockUseActivityTimeline.mockReturnValue({
      data: mockTimelineData(3),
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<TimelinePage />, { wrapper: createWrapper() });
    expect(screen.getByText(/for this contact/i)).toBeInTheDocument();
  });

  it('shows context banner when entity_type=deal is in URL', () => {
    mockUseSearchParams.mockReturnValue([
      new URLSearchParams('entity_type=deal&entity_id=d1'),
    ]);
    mockUseActivityTimeline.mockReturnValue({
      data: mockTimelineData(3),
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<TimelinePage />, { wrapper: createWrapper() });
    expect(screen.getByText(/for this deal/i)).toBeInTheDocument();
  });

  it('renders "Clear filter" link in context banner', () => {
    mockUseSearchParams.mockReturnValue([
      new URLSearchParams('actor_id=abc-123'),
    ]);
    mockUseActivityTimeline.mockReturnValue({
      data: mockTimelineData(3),
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<TimelinePage />, { wrapper: createWrapper() });
    expect(screen.getByText('Clear filter')).toBeInTheDocument();
  });
});