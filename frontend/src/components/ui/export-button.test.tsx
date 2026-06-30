import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ExportButton } from './export-button';

// Mock the hook that the button uses internally
vi.mock('../../hooks/useExportCsv', () => ({
  useExportCsv: vi.fn(),
}));

import { useExportCsv } from '../../hooks/useExportCsv';

describe('ExportButton (ui)', () => {
  const mockDownload = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useExportCsv).mockReturnValue({
      download: mockDownload,
      isExporting: false,
    });
  });

  it('renders with default label', () => {
    render(<ExportButton url="/api/export/contacts/" filename="contacts.csv" />);
    expect(screen.getByRole('button', { name: /export csv/i })).toBeInTheDocument();
  });

  it('renders custom label when provided', () => {
    render(
      <ExportButton
        url="/api/export/contacts/"
        filename="contacts.csv"
        label="Download CSV"
      />,
    );
    expect(screen.getByRole('button', { name: /download csv/i })).toBeInTheDocument();
  });

  it('renders all button variants without error', () => {
    const variants = ['primary', 'secondary', 'outline', 'ghost', 'danger'] as const;
    for (const variant of variants) {
      const { unmount } = render(
        <ExportButton
          url="/api/export/deals/"
          filename="deals.csv"
          variant={variant}
        />,
      );
      expect(screen.getByRole('button')).toBeInTheDocument();
      unmount();
    }
  });

  it('renders all sizes without error', () => {
    const sizes = ['sm', 'md', 'lg'] as const;
    for (const size of sizes) {
      const { unmount } = render(
        <ExportButton
          url="/api/export/deals/"
          filename="deals.csv"
          size={size}
        />,
      );
      expect(screen.getByRole('button')).toBeInTheDocument();
      unmount();
    }
  });

  it('calls download with extra params when clicked', async () => {
    const user = userEvent.setup();
    render(
      <ExportButton
        url="/api/export/deals/"
        filename="deals.csv"
        params={{ format: 'csv' }}
      />,
    );
    await user.click(screen.getByRole('button', { name: /export csv/i }));
    expect(mockDownload).toHaveBeenCalledWith({ format: 'csv' });
  });

  it('calls download with undefined params when no params provided', async () => {
    const user = userEvent.setup();
    render(<ExportButton url="/api/export/contacts/" filename="contacts.csv" />);
    await user.click(screen.getByRole('button', { name: /export csv/i }));
    expect(mockDownload).toHaveBeenCalledWith(undefined);
  });

  it('shows loading indicator and disables when isExporting is true', () => {
    vi.mocked(useExportCsv).mockReturnValue({
      download: mockDownload,
      isExporting: true,
    });
    render(<ExportButton url="/api/export/contacts/" filename="contacts.csv" />);
    const btn = screen.getByRole('button', { name: /export csv/i });
    expect(btn).toBeDisabled();
    expect(btn).toHaveAttribute('aria-busy', 'true');
  });
});