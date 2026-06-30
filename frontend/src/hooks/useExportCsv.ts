import { useCallback, useState } from 'react';
import apiClient from '../api/client';
import toast from 'react-hot-toast';

/**
 * Hook to download a CSV blob from an export endpoint and trigger
 * a browser file download.
 *
 * @param url - The API endpoint path (e.g. '/contacts/contacts/export_csv/')
 * @param filename - Default filename for the download
 * @returns { download, isExporting }
 */
export function useExportCsv(url: string, filename: string) {
  const [isExporting, setIsExporting] = useState(false);

  const download = useCallback(
    async (extraParams?: Record<string, string>) => {
      setIsExporting(true);
      try {
        const params = extraParams ?? undefined;
        const response = await apiClient.get(url, {
          params,
          responseType: 'blob',
        });

        // Create a download link and trigger it
        const blob = new Blob([response.data], { type: 'text/csv' });
        const objectUrl = window.URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = objectUrl;
        anchor.download = filename;
        document.body.appendChild(anchor);
        anchor.click();
        document.body.removeChild(anchor);
        window.URL.revokeObjectURL(objectUrl);

        toast.success(`${filename} downloaded`);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Export failed';
        toast.error(msg);
      } finally {
        setIsExporting(false);
      }
    },
    [url, filename],
  );

  return { download, isExporting };
}