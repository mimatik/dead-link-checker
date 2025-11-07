import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
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
  EyeIcon,
} from '@heroicons/react/24/outline';

export default function Dashboard() {
  const navigate = useNavigate();
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
          <div className="dashboard-jobs-grid">
            {/* Header - hidden on mobile */}
            <div className="hidden md:contents">
              <div className="p-4 bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200">
                Status
              </div>
              <div className="p-4 bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200">
                URL
              </div>
              <div className="p-4 bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200">
                Stats
              </div>
              <div className="p-4 bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200">
                Created
              </div>
              <div className="p-4 bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wider text-right border-b border-gray-200">
                Actions
              </div>
            </div>

            {/* Jobs */}
            {jobs.map((job, jobIndex) => (
              <>
                {/* Status */}
                <div key={`${job.id}-status`} className={`flex items-center p-2 md:p-4 ${jobIndex > 0 ? 'md:border-t border-t border-gray-200' : ''}`}>
                  <span className="md:hidden text-xs text-gray-500 mr-2">Status:</span>
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
                </div>

                {/* URL */}
                <div key={`${job.id}-url`} className="flex flex-col md:flex-row md:items-center min-w-0 p-2 md:p-4 md:border-t border-t-0 border-gray-200">
                  <span className="md:hidden text-xs text-gray-500 mb-1">URL:</span>
                  <p className="text-sm font-medium text-gray-900 break-all md:truncate">
                    {job.config.start_url}
                  </p>
                </div>

                {/* Stats */}
                <div key={`${job.id}-stats`} className="flex flex-col md:flex-row md:items-center min-w-0 p-2 md:p-4 md:border-t border-t-0 border-gray-200">
                  <span className="md:hidden text-xs text-gray-500 mb-1">Stats:</span>
                  <div className="flex flex-wrap items-center gap-2 md:gap-4 text-sm text-gray-500">
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
                </div>

                {/* Created */}
                <div key={`${job.id}-created`} className="flex flex-col md:flex-row md:items-center min-w-0 p-2 md:p-4 md:border-t border-t-0 border-gray-200">
                  <span className="md:hidden text-xs text-gray-500 mb-1">Created:</span>
                  <div className="flex items-center text-sm text-gray-500">
                    <ClockIcon className="w-4 h-4 mr-1" />
                    {formatDate(job.created_at)}
                  </div>
                </div>

                {/* Actions */}
                <div key={`${job.id}-actions`} className="flex items-center justify-start md:justify-end p-2 md:p-4 md:border-t border-t-0 border-gray-200">
                  <div className="flex items-center gap-2">
                    {job.report_path && (
                      <>
                        <Button
                          onClick={() =>
                            navigate(`/reports/${job.report_path?.split('/').pop() || ''}`)
                          }
                          variant="icon"
                          title="View Report"
                        >
                          <EyeIcon className="w-5 h-5" />
                        </Button>
                        <Button
                          href={apiClient.getReportDownloadUrl(
                            job.report_path.split('/').pop() || ''
                          )}
                          variant="icon"
                          download
                          title="Download Report"
                          onClick={(e) => {
                            e?.stopPropagation();
                          }}
                        >
                          <ArrowDownTrayIcon className="w-5 h-5" />
                        </Button>
                      </>
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
              </>
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

