import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient, type Config } from '../api/client';
import ConfigModal from '../components/ConfigModal';
import Button from '../components/Button';
import {
  PlusIcon,
  PlayIcon,
  PencilIcon,
  TrashIcon,
  Cog6ToothIcon,
  ClockIcon,
  PauseIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

export default function Configs() {
  const navigate = useNavigate();
  const [configs, setConfigs] = useState<Config[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editingConfig, setEditingConfig] = useState<Config | null>(null);

  useEffect(() => {
    loadConfigs();
  }, []);

  const loadConfigs = async () => {
    try {
      const data = await apiClient.listConfigs();
      setConfigs(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load configs');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this configuration?')) {
      return;
    }

    try {
      await apiClient.deleteConfig(id);
      await loadConfigs();
    } catch (err) {
      alert('Failed to delete configuration: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  const handleRunCheck = async (configId: string) => {
    try {
      await apiClient.startCrawl({ configId });
      // Redirect to dashboard to see the running job
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start check');
    }
  };

  const handleEdit = (config: Config) => {
    setEditingConfig(config);
    setShowModal(true);
  };

  const handleCreate = () => {
    setEditingConfig(null);
    setShowModal(true);
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
          <h2 className="text-2xl sm:text-3xl font-bold text-gray-900">Configurations</h2>
          <p className="mt-1 text-sm text-gray-500">
            Manage and run your configurations
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Button
            onClick={handleCreate}
            variant="primary"
            icon={<PlusIcon className="w-4 h-4" />}
          >
            <span className="hidden sm:inline">New Configuration</span>
            <span className="sm:hidden">New</span>
          </Button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Configs Grid */}
      {configs.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg">
          <Cog6ToothIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            No configurations yet
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            Create your first configuration to get started.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {configs.map((config) => (
            <div
              key={config.id}
              className="bg-white overflow-hidden border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
            >
              <div className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-medium text-gray-900 truncate">
                    {config.name}
                  </h3>
                </div>
                <p className="text-sm text-gray-600 mb-4 truncate">
                  {config.start_url}
                </p>
                <div className="space-y-2 text-sm text-gray-500">
                  <div className="flex items-center">
                    <ClockIcon className="w-4 h-4 mr-2" />
                    Timeout: {config.timeout || 15}s
                  </div>
                  <div className="flex items-center">
                    <PauseIcon className="w-4 h-4 mr-2" />
                    Delay: {config.delay || 0.5}s
                  </div>
                  <div className="flex items-center">
                    <ArrowPathIcon className="w-4 h-4 mr-2" />
                    Max depth: {config.max_depth === null ? '∞' : config.max_depth}
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-5 py-3 flex justify-between border-t border-gray-200">
                <Button
                  onClick={() => handleRunCheck(config.id)}
                  variant="primary"
                  size="sm"
                  icon={<PlayIcon className="w-4 h-4" />}
                >
                  Run
                </Button>
                <div className="flex gap-2">
                  <Button
                    onClick={() => handleEdit(config)}
                    variant="icon"
                    className="text-sm"
                  >
                    <PencilIcon className="w-4 h-4" />
                  </Button>
                  <Button
                    onClick={() => handleDelete(config.id)}
                    variant="icon"
                    className="text-sm !text-red-600 hover:!text-red-700"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal for Create/Edit */}
      {showModal && (
        <ConfigModal
          config={editingConfig}
          onClose={() => {
            setShowModal(false);
            setEditingConfig(null);
          }}
          onSave={async () => {
            await loadConfigs();
            setShowModal(false);
            setEditingConfig(null);
          }}
        />
      )}
    </div>
  );
}

