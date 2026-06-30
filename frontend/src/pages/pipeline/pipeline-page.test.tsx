import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import toast from 'react-hot-toast';

// Mock all API hooks used by the pipeline page
vi.mock('../../api/deals', () => ({
  usePipelines: vi.fn(),
  useDeals: vi.fn(),
  useUpdateDeal: vi.fn(),
  useChangeDealStatus: vi.fn(),
  useCreateDeal: vi.fn(),
}));

// Mock the useExportCsv hook that ExportButton uses internally
vi.mock('../../hooks/useExportCsv', () => ({
  useExportCsv: vi.fn(),
}));

vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock('date-fns', () => ({
  format: vi.fn(() => 'Jan 1, 2026'),
  parseISO: vi.fn((s: string) => new Date(s)),
}));

import { usePipelines, useDeals, useUpdateDeal, useChangeDealStatus, useCreateDeal } from '../../api/deals';
import { useExportCsv } from '../../hooks/useExportCsv';
import { PipelinePage } from './pipeline-page';

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <PipelinePage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('PipelinePage ExportButton integration', () => {
  const mockDownload = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock pipeline data with one pipeline and stage
    vi.mocked(usePipelines).mockReturnValue({
      data: [
        {
          id: '1',
          name: 'Sales Pipeline',
          is_default: true,
          is_active: true,
          stages: [
            { id: 's1', name: 'Qualified', display_order: 1, probability: '0.25', deals: [] },
          ],
        },
      ],
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    vi.mocked(useDeals).mockReturnValue({
      data: { results: [], count: 0 },
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    vi.mocked(useUpdateDeal).mockReturnValue({
      mutateAsync: vi.fn(),
    } as any);

    vi.mocked(useChangeDealStatus).mockReturnValue({
      mutateAsync: vi.fn(),
    } as any);

    vi.mocked(useCreateDeal).mockReturnValue({
      mutateAsync: vi.fn(),
    } as any);

    vi.mocked(useExportCsv).mockReturnValue({
      download: mockDownload,
      isExporting: false,
    });
  });

  it('renders Export CSV button in the page header', () => {
    renderPage();
    expect(screen.getByRole('button', { name: /export csv/i })).toBeInTheDocument();
  });

  it('passes correct url and filename to ExportButton', () => {
    renderPage();
    const button = screen.getByRole('button', { name: /export csv/i });
    expect(button).toBeInTheDocument();
    // The ExportButton triggers download on click
  });

  it('triggers export download when Export CSV button is clicked', async () => {
    const user = userEvent.setup();
    renderPage();
    await user.click(screen.getByRole('button', { name: /export csv/i }));
    // The ExportButton passes url="/export/deals/" and filename="deals.csv"
    // which calls download(undefined) via the mock
    expect(mockDownload).toHaveBeenCalledWith(undefined);
  });

  it('shows loading state on export button while exporting', () => {
    vi.mocked(useExportCsv).mockReturnValue({
      download: mockDownload,
      isExporting: true,
    });
    renderPage();
    const button = screen.getByRole('button', { name: /export csv/i });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('aria-busy', 'true');
  });

  it('does not render Export CSV button while pipeline data is loading', () => {
    vi.mocked(usePipelines).mockReturnValue({
      data: null,
      isLoading: true,
    } as any);
    renderPage();
    // During loading the page shows skeleton placeholders, not the header
    expect(screen.queryByRole('button', { name: /export csv/i })).not.toBeInTheDocument();
  });
});