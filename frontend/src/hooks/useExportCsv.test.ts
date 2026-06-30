import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useExportCsv } from './useExportCsv';
import apiClient from '../api/client';
import toast from 'react-hot-toast';

vi.mock('../api/client', () => ({
  default: {
    get: vi.fn(),
  },
}));

// Mock toast as real function with .success and .error
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe('useExportCsv (hooks)', () => {
  const url = '/api/export/contacts/';
  const filename = 'contacts.csv';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('starts with isExporting=false', () => {
    const { result } = renderHook(() => useExportCsv(url, filename));
    expect(result.current.isExporting).toBe(false);
  });

  it('download calls apiClient.get with correct url and params', async () => {
    const blobContent = 'name,email\nAlice,alice@test.com\n';
    vi.mocked(apiClient.get).mockResolvedValue({ data: new Blob([blobContent], { type: 'text/csv' }) });

    vi.spyOn(window.URL, 'createObjectURL').mockReturnValue('blob:http://mock');
    vi.spyOn(window.URL, 'revokeObjectURL').mockImplementation(() => {});
    vi.spyOn(document.body, 'appendChild').mockImplementation(() => document.createElement('a'));
    vi.spyOn(document.body, 'removeChild').mockImplementation(() => document.createElement('a'));

    const { result } = renderHook(() => useExportCsv(url, filename));
    await act(async () => {
      await result.current.download();
    });

    expect(apiClient.get).toHaveBeenCalledWith(url, {
      params: undefined,
      responseType: 'blob',
    });
  });

  it('passes extraParams to apiClient.get when provided', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: new Blob(['a,b\n1,2']) });
    vi.spyOn(window.URL, 'createObjectURL').mockReturnValue('blob:http://mock');
    vi.spyOn(window.URL, 'revokeObjectURL').mockImplementation(() => {});
    vi.spyOn(document.body, 'appendChild').mockImplementation(() => document.createElement('a'));
    vi.spyOn(document.body, 'removeChild').mockImplementation(() => document.createElement('a'));

    const { result } = renderHook(() => useExportCsv(url, filename));
    await act(async () => {
      await result.current.download({ search: 'alice', format: 'csv' });
    });

    expect(apiClient.get).toHaveBeenCalledWith(url, {
      params: { search: 'alice', format: 'csv' },
      responseType: 'blob',
    });
  });

  it('creates download link and triggers click', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: new Blob(['a,b\n1,2'], { type: 'text/csv' }) });

    const mockUrl = 'blob:http://mock-download';
    const createObjectURL = vi.spyOn(window.URL, 'createObjectURL').mockReturnValue(mockUrl);
    const revokeObjectURL = vi.spyOn(window.URL, 'revokeObjectURL').mockImplementation(() => {});
    const appendChild = vi.spyOn(document.body, 'appendChild').mockImplementation(() => document.createElement('a'));
    const removeChild = vi.spyOn(document.body, 'removeChild').mockImplementation(() => document.createElement('a'));

    const { result } = renderHook(() => useExportCsv(url, filename));
    await act(async () => {
      await result.current.download();
    });

    expect(createObjectURL).toHaveBeenCalled();
    expect(appendChild).toHaveBeenCalled();
    // The click() happens on the temp anchor
    expect(removeChild).toHaveBeenCalled();
    expect(revokeObjectURL).toHaveBeenCalledWith(mockUrl);
  });

  it('shows toast.success on successful download', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: new Blob(['a,b\n1,2']) });
    vi.spyOn(window.URL, 'createObjectURL').mockReturnValue('blob:http://mock');
    vi.spyOn(window.URL, 'revokeObjectURL').mockImplementation(() => {});
    vi.spyOn(document.body, 'appendChild').mockImplementation(() => document.createElement('a'));
    vi.spyOn(document.body, 'removeChild').mockImplementation(() => document.createElement('a'));

    const { result } = renderHook(() => useExportCsv(url, filename));
    await act(async () => {
      await result.current.download();
    });

    expect(toast.success).toHaveBeenCalledWith(`${filename} downloaded`);
  });

  it('shows toast.error with error message on API failure', async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new Error('Network error'));
    vi.spyOn(window.URL, 'createObjectURL').mockReturnValue('blob:http://mock');
    vi.spyOn(window.URL, 'revokeObjectURL').mockImplementation(() => {});
    // No DOM calls expected on error, but links may still be created in catch block

    const { result } = renderHook(() => useExportCsv(url, filename));
    await act(async () => {
      await result.current.download();
    });

    expect(toast.error).toHaveBeenCalledWith('Network error');
  });

  it('shows toast.error with fallback when error has no message', async () => {
    vi.mocked(apiClient.get).mockRejectedValue({});
    vi.spyOn(window.URL, 'createObjectURL').mockReturnValue('blob:http://mock');
    vi.spyOn(window.URL, 'revokeObjectURL').mockImplementation(() => {});

    const { result } = renderHook(() => useExportCsv(url, filename));
    await act(async () => {
      await result.current.download();
    });

    expect(toast.error).toHaveBeenCalledWith('Export failed');
  });

  it('sets isExporting to true during download and false after', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: new Blob(['a,b\n1,2']) });
    vi.spyOn(window.URL, 'createObjectURL').mockReturnValue('blob:http://mock');
    vi.spyOn(window.URL, 'revokeObjectURL').mockImplementation(() => {});
    vi.spyOn(document.body, 'appendChild').mockImplementation(() => document.createElement('a'));
    vi.spyOn(document.body, 'removeChild').mockImplementation(() => document.createElement('a'));

    const { result } = renderHook(() => useExportCsv(url, filename));

    let downloadPromise: Promise<void>;
    act(() => {
      downloadPromise = result.current.download();
    });

    // During download
    expect(result.current.isExporting).toBe(true);

    await act(async () => {
      await downloadPromise;
    });

    // After download completes
    expect(result.current.isExporting).toBe(false);
  });

  it('sets isExporting to false even when download fails', async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new Error('Failed'));

    const { result } = renderHook(() => useExportCsv(url, filename));
    await act(async () => {
      await result.current.download();
    });

    expect(result.current.isExporting).toBe(false);
  });
});