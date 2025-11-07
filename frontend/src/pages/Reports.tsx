import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient, type Report } from '../api/client';
import Button from '../components/Button';
import {
  DocumentTextIcon,
  ArrowDownTrayIcon,
  ClockIcon,
  FolderIcon,
  DocumentMagnifyingGlassIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';

export default function Reports() {
  const navigate = useNavigate();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      const data = await apiClient.listReports();
      setReports(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load reports');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteReport = async (filename: string) => {
    if (!confirm(`Opravdu chcete smazat report "${filename}"?`)) {
      return;
    }

    try {
      await apiClient.deleteReport(filename);
      await loadReports(); // Refresh reports list
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete report');
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (timestamp: number): string => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div>
          <h2 className="text-2xl sm:text-3xl font-bold text-gray-900">Reports</h2>
          <p className="mt-1 text-sm text-gray-500">
            Download and view crawl reports
          </p>
        </div>
        <div className="flex items-center space-x-3">
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Reports List */}
      {reports.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg">
          <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No reports yet</h3>
          <p className="mt-1 text-sm text-gray-500">
            Reports will appear here after you run crawls.
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="reports-grid">
            {/* Header - hidden on mobile */}
            <div className="hidden md:contents">
              <div className="p-4 bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200">
                Name
              </div>
              <div className="p-4 bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200">
                Size
              </div>
              <div className="p-4 bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200">
                Created
              </div>
              <div className="p-4 bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wider text-right border-b border-gray-200">
                Actions
              </div>
            </div>

            {/* Reports */}
            {reports.map((report, reportIndex) => (
              <>
                {/* Name */}
                <div
                  key={`${report.filename}-name`}
                  className={`flex items-center p-2 md:p-4 cursor-pointer ${reportIndex > 0 ? 'md:border-t border-t border-gray-200' : ''}`}
                  onClick={() => navigate(`/reports/${report.filename}`)}
                >
                  <DocumentTextIcon className="w-5 h-5 text-gray-400 mr-3 flex-shrink-0" />
                  <p className="text-sm font-medium text-gray-900 break-all md:truncate">
                    {report.filename}
                  </p>
                </div>

                {/* Size */}
                <div
                  key={`${report.filename}-size`}
                  className="flex flex-col md:flex-row md:items-center min-w-0 p-2 md:p-4 md:border-t border-t-0 border-gray-200"
                >
                  <span className="md:hidden text-xs text-gray-500 mb-1">Size:</span>
                  <div className="flex items-center text-sm text-gray-500">
                    <FolderIcon className="w-4 h-4 mr-1" />
                    {formatFileSize(report.size)}
                  </div>
                </div>

                {/* Created */}
                <div
                  key={`${report.filename}-created`}
                  className="flex flex-col md:flex-row md:items-center min-w-0 p-2 md:p-4 md:border-t border-t-0 border-gray-200"
                >
                  <span className="md:hidden text-xs text-gray-500 mb-1">Created:</span>
                  <div className="flex items-center text-sm text-gray-500">
                    <ClockIcon className="w-4 h-4 mr-1" />
                    {formatDate(report.created_at)}
                  </div>
                </div>

                {/* Actions */}
                <div
                  key={`${report.filename}-actions`}
                  className="flex items-center justify-start md:justify-end p-2 md:p-4 md:border-t border-t-0 border-gray-200"
                  onClick={(e) => e.stopPropagation()}
                >
                  <div className="flex items-center gap-2">
                    <Button
                      onClick={() => navigate(`/reports/${report.filename}`)}
                      variant="icon"
                      title="View Report"
                    >
                      <DocumentMagnifyingGlassIcon className="w-5 h-5" />
                    </Button>
                    <Button
                      href={apiClient.getReportDownloadUrl(report.filename)}
                      variant="icon"
                      download
                      title="Download Report"
                    >
                      <ArrowDownTrayIcon className="w-5 h-5" />
                    </Button>
                    <Button
                      onClick={() => handleDeleteReport(report.filename)}
                      variant="icon"
                      title="Delete Report"
                    >
                      <TrashIcon className="w-5 h-5" />
                    </Button>
                  </div>
                </div>
              </>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

