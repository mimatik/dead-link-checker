import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient, type Config } from '../api/client';
import ConfigModal from '../components/ConfigModal';

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
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Website Checks</h2>
          <p className="mt-1 text-sm text-gray-500">
            Manage and run your website checks
          </p>
        </div>
        <button
          onClick={handleCreate}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
        >
          <span className="mr-2">+</span>
          New Website Check
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Configs Grid */}
      {configs.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <span className="text-6xl">⚙️</span>
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
              className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow"
            >
              <div className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-medium text-gray-900 truncate">
                    {config.name}
                  </h3>
                </div>
                <p className="text-sm text-blue-600 mb-4 truncate">
                  {config.start_url}
                </p>
                <div className="space-y-1 text-sm text-gray-500">
                  <p>⏱ Timeout: {config.timeout || 15}s</p>
                  <p>⏸ Delay: {config.delay || 0.5}s</p>
                  <p>
                    📏 Max depth: {config.max_depth === null ? '∞' : config.max_depth}
                  </p>
                </div>
              </div>
              <div className="bg-gray-50 px-5 py-3 flex justify-between">
                <button
                  onClick={() => handleRunCheck(config.id)}
                  className="inline-flex items-center px-3 py-1.5 border border-transparent rounded-md text-sm font-medium text-white bg-green-600 hover:bg-green-700"
                >
                  ▶ Run Check
                </button>
                <div className="flex space-x-3">
                  <button
                    onClick={() => handleEdit(config)}
                    className="text-sm text-blue-600 hover:text-blue-500 font-medium"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(config.id)}
                    className="text-sm text-red-600 hover:text-red-500 font-medium"
                  >
                    Delete
                  </button>
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

