import { useEffect, useState } from 'react';
import { apiClient, type Job } from '../api/client';
import ConfigModal from '../components/ConfigModal';
import Button from '../components/Button';
import {
  PlayIcon,
  ArrowPathIcon,
  XMarkIcon,
  ArrowDownTrayIcon,
  DocumentTextIcon,
  LinkIcon,
  ExclamationTriangleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';

export default function Dashboard() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showConfigModal, setShowConfigModal] = useState(false);

  useEffect(() => {
    loadJobs();
    const interval = setInterval(loadJobs, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const loadJobs = async () => {
    try {
      const data = await apiClient.listJobs(10);
      setJobs(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load jobs');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelJob = async (jobId: string) => {
    if (!confirm('Opravdu chcete zrušit tento crawl job?')) {
      return;
    }

    try {
      await apiClient.cancelJob(jobId);
      await loadJobs(); // Refresh jobs list
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel job');
    }
  };

  const handleRerunJob = async (job: Job) => {
    try {
      // Use the config from the job to rerun it
      if (job.config_id) {
        await apiClient.startCrawl({ configId: job.config_id });
      } else {
        // If no config_id, use the config directly
        await apiClient.startCrawl({ config: job.config });
      }
      await loadJobs(); // Refresh jobs list
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to rerun job');
    }
  };

  const handleCreateConfigAndRun = () => {
    setShowConfigModal(true);
  };

  const getStatusColor = (status: Job['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'queued':
        return 'bg-amber-100 text-amber-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
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
          <h2 className="text-2xl sm:text-3xl font-bold text-gray-900">Dashboard</h2>
          <p className="mt-1 text-sm text-gray-500">
            Recent crawl jobs and their status (auto-refresh every 5s)
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Button
            onClick={handleCreateConfigAndRun}
            variant="primary"
            icon={<PlayIcon className="w-4 h-4" />}
          >
            <span className="hidden sm:inline">New Check</span>
            <span className="sm:hidden">New</span>
          </Button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="rounded-lg bg-red-50 p-4 border border-red-200">
          <div className="flex">
            <div className="flex-shrink-0">
              <ExclamationTriangleIcon className="w-5 h-5 text-red-400" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
            </div>
          </div>
        </div>
      )}

      {/* Jobs List */}
      {jobs.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg">
          <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No jobs yet</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by running your first check.
          </p>
          <div className="mt-6">
            <Button
              onClick={handleCreateConfigAndRun}
              variant="primary"
              icon={<PlayIcon className="w-4 h-4" />}
            >
              Run New Check
            </Button>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          {/* Desktop Table */}
          <div className="hidden md:block overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    URL
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Stats
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2.5 py-1 inline-flex text-xs leading-5 font-semibold rounded-md ${getStatusColor(
                          job.status
                        )}`}
                      >
                        {job.status === 'running' ? (
                          <span className="flex items-center">
                            <span className="w-2 h-2 bg-current rounded-full mr-1.5 animate-pulse"></span>
                            {job.status}
                          </span>
                        ) : (
                          job.status
                        )}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-sm font-medium text-gray-900 truncate max-w-xs">
                        {job.config.start_url}
                      </p>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <span className="flex items-center">
                          <DocumentTextIcon className="w-4 h-4 mr-1" />
                          {job.stats.pages_crawled}
                        </span>
                        <span className="flex items-center">
                          <LinkIcon className="w-4 h-4 mr-1" />
                          {job.stats.links_checked}
                        </span>
                        {job.stats.errors_found > 0 && (
                          <span className="flex items-center text-red-600">
                            <ExclamationTriangleIcon className="w-4 h-4 mr-1" />
                            {job.stats.errors_found}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="flex items-center">
                        <ClockIcon className="w-4 h-4 mr-1" />
                        {formatDate(job.created_at)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end space-x-3">
                        {job.report_path && (
                          <a
                            href={apiClient.getReportDownloadUrl(
                              job.report_path.split('/').pop() || ''
                            )}
                            className="text-gray-600 hover:text-gray-900"
                            download
                            title="Download Report"
                          >
                            <ArrowDownTrayIcon className="w-5 h-5" />
                          </a>
                        )}
                        {(job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') && (
                          <Button
                            onClick={() => handleRerunJob(job)}
                            variant="icon"
                            title="Rerun"
                          >
                            <ArrowPathIcon className="w-5 h-5" />
                          </Button>
                        )}
                        {(job.status === 'running' || job.status === 'queued') && (
                          <Button
                            onClick={() => handleCancelJob(job.id)}
                            variant="danger"
                            size="sm"
                            icon={<XMarkIcon className="w-4 h-4" />}
                          >
                            Cancel
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile Cards */}
          <div className="md:hidden divide-y divide-gray-200">
            {jobs.map((job) => (
              <div key={job.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between mb-3">
                  <span
                    className={`px-2.5 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(
                      job.status
                    )}`}
                  >
                    {job.status === 'running' ? (
                      <span className="flex items-center">
                        <span className="w-2 h-2 bg-current rounded-full mr-1.5 animate-pulse"></span>
                        {job.status}
                      </span>
                    ) : (
                      job.status
                    )}
                  </span>
                  <div className="flex items-center space-x-2">
                    {job.report_path && (
                      <a
                        href={apiClient.getReportDownloadUrl(
                          job.report_path.split('/').pop() || ''
                        )}
                        className="text-gray-600 hover:text-gray-900"
                        download
                        title="Download Report"
                      >
                        <ArrowDownTrayIcon className="w-5 h-5" />
                      </a>
                    )}
                    {(job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') && (
                      <Button
                        onClick={() => handleRerunJob(job)}
                        variant="icon"
                        title="Rerun"
                      >
                        <ArrowPathIcon className="w-5 h-5" />
                      </Button>
                    )}
                    {(job.status === 'running' || job.status === 'queued') && (
                      <Button
                        onClick={() => handleCancelJob(job.id)}
                        variant="danger"
                        size="sm"
                        icon={<XMarkIcon className="w-4 h-4" />}
                      >
                        Cancel
                      </Button>
                    )}
                  </div>
                </div>
                <p className="text-sm font-medium text-gray-900 mb-2 break-all">
                  {job.config.start_url}
                </p>
                <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500 mb-2">
                  <span className="flex items-center">
                    <DocumentTextIcon className="w-4 h-4 mr-1" />
                    {job.stats.pages_crawled} pages
                  </span>
                  <span className="flex items-center">
                    <LinkIcon className="w-4 h-4 mr-1" />
                    {job.stats.links_checked} links
                  </span>
                  {job.stats.errors_found > 0 && (
                    <span className="flex items-center text-red-600">
                      <ExclamationTriangleIcon className="w-4 h-4 mr-1" />
                      {job.stats.errors_found} errors
                    </span>
                  )}
                </div>
                <div className="flex items-center text-sm text-gray-500">
                  <ClockIcon className="w-4 h-4 mr-1" />
                  {formatDate(job.created_at)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Config Modal for creating new config and running crawl */}
      {showConfigModal && (
        <ConfigModal
          config={null}
          onClose={() => {
            setShowConfigModal(false);
          }}
          onSave={async (configId?: string) => {
            setShowConfigModal(false);
            // Start crawl with the newly created config
            try {
              if (configId) {
                await apiClient.startCrawl({ configId });
              }
              await loadJobs(); // Refresh jobs list
            } catch (err) {
              setError(err instanceof Error ? err.message : 'Failed to start crawl');
            }
          }}
          saveButtonText="Save & Run"
        />
      )}
    </div>
  );
}

