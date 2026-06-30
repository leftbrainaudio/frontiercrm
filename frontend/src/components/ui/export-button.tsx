import { Download } from 'lucide-react';
import { Button } from '../atoms/button';
import { useExportCsv } from '../../hooks/useExportCsv';

interface ExportButtonProps {
  /** API endpoint path (e.g. '/contacts/contacts/export_csv/') */
  url: string;
  /** Filename for the downloaded CSV (e.g. 'contacts.csv', 'deals.csv') */
  filename: string;
  /** Optional extra query params to send with the export request */
  params?: Record<string, string>;
  /** Optional label override (default: 'Export') */
  label?: string;
  /** Button variant (default: 'secondary') */
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  /** Button size (default: 'sm') */
  size?: 'sm' | 'md' | 'lg';
}

export function ExportButton({
  url,
  filename,
  params,
  label = 'Export CSV',
  variant = 'secondary',
  size = 'sm',
}: ExportButtonProps) {
  const { download, isExporting } = useExportCsv(url, filename);

  return (
    <Button
      variant={variant}
      size={size}
      loading={isExporting}
      icon={<Download className="h-4 w-4" />}
      onClick={() => download(params)}
    >
      {label}
    </Button>
  );
}