import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiClient, type ReportData, type ReportEntry, type Config } from '../api/client';
import {
  ArrowDownTrayIcon,
  CheckCircleIcon,
  ArrowLeftIcon,
  LinkIcon,
  ChartBarIcon,
  TrashIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import Button from '../components/Button';

// Helper function to extract domain from URL
const extractDomain = (url: string): string => {
  try {
    const urlObj = new URL(url);
    return urlObj.hostname.replace('www.', '');
  } catch {
    return '';
  }
};

// Helper function to extract status code from error_type
const extractStatusCode = (errorType: string): number | null => {
  if (errorType.startsWith('HTTP ')) {
    const match = errorType.match(/HTTP (\d+)/);
    if (match) {
      return parseInt(match[1], 10);
    }
  }
  return null;
};

// Helper function to check if error_type is Timeout or Connection Error
const isTimeoutOrConnection = (errorType: string): boolean => {
  const lower = errorType.toLowerCase();
  return lower.includes('timeout') || lower.includes('connection error');
};

// Check if entry matches a domain rule in config
const checkEntryHasRule = (entry: ReportEntry, config: Config | null): boolean => {
  if (!config || !config.domain_rules) {
    return false;
  }

  const domain = extractDomain(entry.link_url);
  if (!domain) {
    return false;
  }

  const domainRule = config.domain_rules[domain];
  if (!domainRule) {
    return false;
  }

  const statusCode = extractStatusCode(entry.error_type);
  const isTimeoutConn = isTimeoutOrConnection(entry.error_type);

  // Check if status code is in allowed_codes
  if (statusCode !== null && domainRule.allowed_codes?.includes(statusCode)) {
    return true;
  }

  // Check if ignore_timeouts is set for timeout/connection errors
  if (isTimeoutConn && domainRule.ignore_timeouts) {
    return true;
  }

  return false;
};

export default function ReportDetail() {
  const { filename } = useParams<{ filename: string }>();
  const navigate = useNavigate();
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [config, setConfig] = useState<Config | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resolving, setResolving] = useState<string | null>(null);
  const [removing, setRemoving] = useState<string | null>(null);
  const [resolvedLinks, setResolvedLinks] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (filename) {
      loadReportData();
    }
  }, [filename]);

  const loadReportData = async () => {
    if (!filename) return;

    try {
      setLoading(true);
      const data = await apiClient.getReportData(filename);
      setReportData(data);
      
      // Load config if config_id is available
      if (data.config_id) {
        try {
          const configData = await apiClient.getConfig(data.config_id);
          setConfig(configData);
        } catch (err) {
          // Config not found - that's okay, we'll just not show rules
          console.warn('Config not found:', err);
          setConfig(null);
        }
      } else {
        setConfig(null);
      }
      
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load report data');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkResolved = async (entry: ReportEntry) => {
    if (!filename) return;

    setResolving(entry.link_url);

    try {
      await apiClient.markLinkResolved(
        filename,
        entry.link_url,
        entry.error_type,
        reportData?.config_id || undefined
      );
      setResolvedLinks((prev) => new Set([...prev, entry.link_url]));
      // Reload data to update config and stats
      await loadReportData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to mark link as resolved');
    } finally {
      setResolving(null);
    }
  };

  const handleRemoveRule = async (entry: ReportEntry) => {
    if (!filename) return;

    setRemoving(entry.link_url);

    try {
      await apiClient.removeDomainRule(
        filename,
        entry.link_url,
        entry.error_type,
        reportData?.config_id || undefined
      );
      // Remove from resolvedLinks since rule was removed
      setResolvedLinks((prev) => {
        const newSet = new Set(prev);
        newSet.delete(entry.link_url);
        return newSet;
      });
      // Reload data to update config
      await loadReportData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to remove rule');
    } finally {
      setRemoving(null);
    }
  };

  const handleDeleteReport = async () => {
    if (!filename) return;

    if (!confirm(`Opravdu chcete smazat report "${filename}"?`)) {
      return;
    }

    try {
      await apiClient.deleteReport(filename);
      navigate('/reports'); // Navigate back to reports list
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete report');
    }
  };

  const getErrorTypeColor = (errorType: string) => {
    if (errorType.includes('404')) return 'text-red-600 bg-red-50';
    if (errorType.includes('403')) return 'text-orange-600 bg-orange-50';
    if (errorType.includes('500')) return 'text-red-700 bg-red-100';
    if (errorType.includes('Timeout')) return 'text-yellow-600 bg-yellow-50';
    return 'text-gray-600 bg-gray-50';
  };

  const openLink = (url: string) => {
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (error || !reportData) {
    return (
      <div className="space-y-6">
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-700">{error || 'Report not found'}</p>
        </div>
        <Button onClick={() => navigate('/reports')} icon={<ArrowLeftIcon className="w-4 h-4" />}>
          Back to Reports
        </Button>
      </div>
    );
  }

  // Show all entries, but mark resolved ones
  const allEntries = reportData.entries;
  const resolvedCount = resolvedLinks.size;
  const unresolvedCount = allEntries.length - resolvedCount;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div className="flex items-center gap-4">
          <Button
            onClick={() => navigate('/reports')}
            variant="icon"
            title="Back to Reports"
          >
            <ArrowLeftIcon className="w-5 h-5" />
          </Button>
          <div>
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900">Report Detail</h2>
            <p className="mt-1 text-sm text-gray-500">{reportData.filename}</p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <a
            href={apiClient.getReportDownloadUrl(reportData.filename)}
            download
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
            Download CSV
          </a>
          <Button
            onClick={handleDeleteReport}
            variant="secondary"
            icon={<TrashIcon className="w-4 h-4 text-red-600" />}
            className="text-red-600 hover:text-red-700 border-red-300 hover:border-red-400"
          >
            Delete Report
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center mb-4">
          <ChartBarIcon className="w-5 h-5 text-gray-400 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">Statistics</h3>
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-500">Total Links</div>
            <div className="text-2xl font-bold text-gray-900">{reportData.stats.total}</div>
          </div>
          <div className="bg-red-50 rounded-lg p-4">
            <div className="text-sm text-red-600">Unresolved</div>
            <div className="text-2xl font-bold text-red-700">{unresolvedCount}</div>
          </div>
          <div className="bg-green-50 rounded-lg p-4">
            <div className="text-sm text-green-600">Resolved</div>
            <div className="text-2xl font-bold text-green-700">{resolvedCount}</div>
          </div>
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="text-sm text-blue-600">Error Types</div>
            <div className="text-2xl font-bold text-blue-700">
              {Object.keys(reportData.stats.error_types).length}
            </div>
          </div>
        </div>

        {/* Error Types Breakdown */}
        {Object.keys(reportData.stats.error_types).length > 0 && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Error Types Breakdown</h4>
            <div className="flex flex-wrap gap-2">
              {Object.entries(reportData.stats.error_types).map(([errorType, count]) => (
                <span
                  key={errorType}
                  className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${getErrorTypeColor(
                    errorType
                  )}`}
                >
                  {errorType}: {count}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Entries List */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Reported Links</h3>
          <p className="text-sm text-gray-500 mt-1">
            Links with green background have rules configured. Click on a link to test it, or mark it as resolved.
          </p>
        </div>

        {allEntries.length === 0 ? (
          <div className="text-center py-12">
            <CheckCircleIcon className="mx-auto h-12 w-12 text-green-500" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No links in report</h3>
          </div>
        ) : (
          <div className="report-table-grid">
            {/* Header - hidden on mobile */}
            <div className="hidden md:contents">
              <div className="p-2 bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200">
                Error Type
              </div>
              <div className="p-2 bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200">
                Link URL
              </div>
              <div className="p-2 bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200">
                Link Text
              </div>
              <div className="p-2 bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200">
                Source Page
              </div>
              <div className="p-2 bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wider text-right border-b border-gray-200">
                Actions
              </div>
            </div>

            {/* Entries */}
            {allEntries.map((entry, index) => {
              const isResolved = resolvedLinks.has(entry.link_url);
              const hasRule = checkEntryHasRule(entry, config);
              const cellBgClass = hasRule || isResolved ? 'bg-green-50' : 'bg-white';
              const cellBorderClass = hasRule ? 'border-green-200' : 'border-gray-200';

              return (
                <div key={`${index}-row`} className="contents">
                  {/* Error Type */}
                  <div
                    className={`flex items-center p-2 md:border-t border-t'
                    } ${cellBgClass} ${cellBorderClass}`}
                  >
                    <span className="md:hidden text-xs text-gray-500 mr-2">Error Type:</span>
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getErrorTypeColor(
                        entry.error_type
                      )}`}
                    >
                      {entry.error_type}
                    </span>
                  </div>

                  {/* Link URL */}
                  <div
                    className={`flex flex-col md:flex-row md:items-center min-w-0 p-2 md:border-t border-t-0'
                    } ${cellBgClass} ${cellBorderClass}`}
                  >
                    <span className="md:hidden text-xs text-gray-500 mb-1">Link URL:</span>
                    <div className="flex items-center min-w-0 flex-1">
                      <a
                        href={entry.link_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-blue-600 hover:text-blue-800 break-all md:truncate flex-1"
                        onClick={(e) => {
                          e.preventDefault();
                          openLink(entry.link_url);
                        }}
                      >
                        {entry.link_url}
                      </a>
                      <LinkIcon className="w-4 h-4 ml-2 text-gray-400 flex-shrink-0" />
                    </div>
                  </div>

                  {/* Link Text */}
                  <div
                    className={`flex flex-col md:flex-row md:items-center min-w-0 p-2 md:border-t border-t-0 ${cellBgClass} ${cellBorderClass}`}
                  >
                    <span className="md:hidden text-xs text-gray-500 mb-1">Link Text:</span>
                    <p className="text-sm text-gray-900 break-all md:truncate">
                      {entry.link_text || '(no text)'}
                    </p>
                  </div>

                  {/* Source Page */}
                  <div
                    className={`flex flex-col md:flex-row md:items-center min-w-0 p-2 md:border-t border-t-0 ${cellBgClass} ${cellBorderClass}`}
                  >
                    <span className="md:hidden text-xs text-gray-500 mb-1">Source Page:</span>
                    <a
                      href={entry.source_page}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-gray-600 hover:text-gray-800 break-all md:truncate"
                    >
                      {entry.source_page}
                    </a>
                  </div>

                  {/* Actions */}
                  <div
                    className={`flex items-center justify-start md:justify-end gap-2 pb-3 md:pb-2 p-2 md:border-t border-t-0 ${cellBgClass} ${cellBorderClass}`}
                  >
                    {hasRule &&  (
                      <Button
                        onClick={() => handleRemoveRule(entry)}
                        variant="secondary"
                        size="sm"
                        disabled={removing === entry.link_url}
                        className="text-gray-600 hover:text-gray-800 border-gray-300"
                      >
                        {removing === entry.link_url ? (
                          'Removing...'
                        ) : (
                          <>
                            <XMarkIcon className="w-4 h-4 mr-1" />
                            <span className="hidden md:inline">Remove rule</span>
                          </>
                        )}
                      </Button>
                    )}
                    {!isResolved && !hasRule && (
                      <Button
                        onClick={() => handleMarkResolved(entry)}
                        variant="primary"
                        size="sm"
                        disabled={resolving === entry.link_url}
                      >
                        {resolving === entry.link_url ? (
                          'Processing...'
                        ) : (
                          <>
                            <CheckCircleIcon className="w-4 h-4 mr-1" />
                            <span className="md:inline">Mark as working</span>
                          </>
                        )}
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
