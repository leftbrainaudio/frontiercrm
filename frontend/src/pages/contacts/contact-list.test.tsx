import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

vi.mock('../../api/contacts', () => ({
  useContacts: vi.fn(),
}));

vi.mock('../../hooks/useExportCsv', () => ({
  useExportCsv: vi.fn(),
}));

import { useContacts } from '../../api/contacts';
import { useExportCsv } from '../../hooks/useExportCsv';
import { ContactListPage } from './contact-list';

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ContactListPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('ContactListPage ExportButton integration', () => {
  const mockDownload = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useContacts).mockReturnValue({
      data: { results: [], count: 0 },
      isLoading: false,
      isError: false,
      error: null,
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

  it('triggers export download when Export CSV button is clicked', async () => {
    const user = userEvent.setup();
    renderPage();
    await user.click(screen.getByRole('button', { name: /export csv/i }));
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

  it('renders ExportButton even while contacts are loading', () => {
    // Unlike the pipeline page, the contacts page renders the header
    // with ExportButton even during the loading state
    vi.mocked(useContacts).mockReturnValue({
      data: null,
      isLoading: true,
    } as any);
    renderPage();
    expect(screen.getByRole('button', { name: /export csv/i })).toBeInTheDocument();
  });
});