import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import IntegrationCard from '../../components/Integrations/IntegrationCard';
import SyncProgressModal from '../../components/Integrations/SyncProgressModal';

interface Integration {
  id: string;
  provider_name: string;
  provider_type: string;
  status: string;
  last_sync_at: string | null;
}

const Integrations = () => {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncModalOpen, setSyncModalOpen] = useState(false);
  const [syncingProvider, setSyncingProvider] = useState<string | null>(null);
  const [syncResult, setSyncResult] = useState<any>(null);

  const fetchIntegrations = async () => {
    try {
      setLoading(true);
      const res = await api.get('/integrations/');
      setIntegrations(res.data);
    } catch (err) {
      console.error('Failed to fetch integrations', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIntegrations();
  }, []);

  const handleConnect = async (providerName: string, providerType: string) => {
    try {
      await api.post('/integrations/', {
        provider_name: providerName,
        provider_type: providerType,
        credentials: {},
      });
      fetchIntegrations();
    } catch (err) {
      console.error('Failed to connect', err);
    }
  };

  const handleTestConnection = async (id: string) => {
    try {
      await api.post(`/integrations/${id}/test`);
      alert('Connection successful!');
    } catch (err) {
      alert('Connection failed!');
    }
  };

  const handleSync = async (id: string, providerName: string) => {
    try {
      setSyncingProvider(providerName);
      setSyncModalOpen(true);
      setSyncResult(null);
      const res = await api.post(`/integrations/${id}/sync`);
      setSyncResult(res.data);
      fetchIntegrations();
    } catch (err) {
      setSyncResult({ status: 'Failed', message: 'Sync failed' });
    }
  };

  const handleDisconnect = async (id: string) => {
    try {
      await api.post(`/integrations/${id}/disconnect`);
      fetchIntegrations();
    } catch (err) {
      console.error('Failed to disconnect', err);
    }
  };

  if (loading) return <div className="p-8">Loading integrations...</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-8 text-gray-900">Data Sources</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <IntegrationCard
          title="Demo HRIS"
          description="Connect to a simulated HRIS system for employee data."
          providerName="demo_hris"
          providerType="hris"
          integration={integrations.find((i) => i.provider_name === 'demo_hris')}
          onConnect={() => handleConnect('demo_hris', 'hris')}
          onTest={() => handleTestConnection(integrations.find((i) => i.provider_name === 'demo_hris')!.id)}
          onSync={() => handleSync(integrations.find((i) => i.provider_name === 'demo_hris')!.id, 'Demo HRIS')}
          onDisconnect={() => handleDisconnect(integrations.find((i) => i.provider_name === 'demo_hris')!.id)}
        />
        
        <IntegrationCard
          title="Demo ERP"
          description="Connect to a simulated ERP system for workforce data."
          providerName="demo_erp"
          providerType="erp"
          integration={integrations.find((i) => i.provider_name === 'demo_erp')}
          onConnect={() => handleConnect('demo_erp', 'erp')}
          onTest={() => handleTestConnection(integrations.find((i) => i.provider_name === 'demo_erp')!.id)}
          onSync={() => handleSync(integrations.find((i) => i.provider_name === 'demo_erp')!.id, 'Demo ERP')}
          onDisconnect={() => handleDisconnect(integrations.find((i) => i.provider_name === 'demo_erp')!.id)}
        />
        
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-xl font-semibold mb-2">CSV Upload</h3>
            <p className="text-gray-500 mb-4">Manually upload workforce data via CSV file.</p>
          </div>
          <div className="flex gap-2">
            <a href="/dashboard/workforce/import" className="w-full text-center bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition">
              Go to Import
            </a>
          </div>
        </div>
      </div>
      
      {syncModalOpen && (
        <SyncProgressModal 
          provider={syncingProvider} 
          result={syncResult} 
          onClose={() => setSyncModalOpen(false)} 
        />
      )}
    </div>
  );
};

export default Integrations;
