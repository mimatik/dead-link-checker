import { useEffect, useState } from 'react';
import { apiClient, type Job } from '../api/client';
import ConfigModal from '../components/ConfigModal';

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
        return 'bg-yellow-100 text-yellow-800';
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
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Dashboard</h2>
          <p className="mt-1 text-sm text-gray-500">
            Recent crawl jobs and their status (auto-refresh every 5s)
          </p>
        </div>
        <button
          onClick={handleCreateConfigAndRun}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <span className="mr-2">▶</span>
          Run New Check
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <span className="text-red-400">⚠️</span>
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
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <span className="text-6xl">📋</span>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No jobs yet</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by running your first check.
          </p>
          <div className="mt-6">
            <button
              onClick={handleCreateConfigAndRun}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
            >
              Run New Check
            </button>
          </div>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {jobs.map((job) => (
              <li key={job.id}>
                <div className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-3">
                        <span
                          className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(
                            job.status
                          )}`}
                        >
                          
                          {job.status === 'running' ? (
                            <span className="ml-1 animate-pulse">
                              {job.status} ●
                            </span>
                          ) : job.status}
                        </span>
                        <p className="text-sm font-medium text-blue-600 truncate">
                          {job.config.start_url}
                        </p>
                      </div>
                      <div className="mt-2 flex items-center text-sm text-gray-500 space-x-4">
                        <span className="font-medium">
                          📊 {job.stats.pages_crawled} pages
                        </span>
                        <span className="font-medium">
                          🔗 {job.stats.links_checked} links
                        </span>
                        {job.stats.errors_found > 0 && (
                          <span className="font-medium">
                            ❌ {job.stats.errors_found} errors
                          </span>
                        )}
                        <span>🕐 {formatDate(job.created_at)}</span>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      {(job.status === 'running' || job.status === 'queued') && (
                        <button
                          onClick={() => handleCancelJob(job.id)}
                          className="flex-shrink-0 px-3 py-1.5 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md"
                        >
                          Cancel
                        </button>
                      )}
                      {job.report_path && (
                        <a
                          href={apiClient.getReportDownloadUrl(
                            job.report_path.split('/').pop() || ''
                          )}
                          className="flex-shrink-0 text-sm font-medium text-blue-600 hover:text-blue-500"
                          download
                        >
                          Download Report
                        </a>
                      )}
                      {(job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') && (
                        <button
                          onClick={() => handleRerunJob(job)}
                          className="flex-shrink-0 text-green-600 hover:text-green-700 text-lg"
                          title="Rerun"
                        >
                          🔄
                        </button>
                      )}
                    </div>
                  </div>
                  {job.error && (
                    <div className="mt-2 text-sm text-red-600">
                      Error: {job.error}
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ul>
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

