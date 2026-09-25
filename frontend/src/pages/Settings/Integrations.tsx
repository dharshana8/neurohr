import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import IntegrationCard from '../../components/Integrations/IntegrationCard';
import SyncProgressModal from '../../components/Integrations/SyncProgressModal';
import { Database, FileSpreadsheet, History, RefreshCw, CheckCircle2, XCircle, AlertTriangle, ArrowUpRight } from 'lucide-react';
import { Link } from 'react-router-dom';

interface Integration {
  id: string;
  integration_id?: string;
  provider_name: string;
  provider_type: string;
  status: string;
  last_sync_at: string | null;
}

interface SyncLogItem {
  id: string;
  integration_id: string;
  status: string;
  records_fetched: number;
  records_created: number;
  records_updated: number;
  records_failed: number;
  started_at: string;
  message?: string;
}

const Integrations = () => {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncModalOpen, setSyncModalOpen] = useState(false);
  const [syncingProvider, setSyncingProvider] = useState<string | null>(null);
  const [syncResult, setSyncResult] = useState<any>(null);
  const [syncLogs, setSyncLogs] = useState<SyncLogItem[]>([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [notice, setNotice] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchIntegrations = async () => {
    try {
      setLoading(true);
      const res = await api.get('/integrations');
      setIntegrations(res.data);
      fetchAllSyncLogs(res.data);
    } catch (err) {
      console.error('Failed to fetch integrations', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAllSyncLogs = async (currentIntegrations: Integration[]) => {
    try {
      setLogsLoading(true);
      const logPromises = currentIntegrations.map(async (intg) => {
        try {
          const logRes = await api.get(`/integrations/${intg.integration_id || intg.id}/sync-logs`);
          return logRes.data;
        } catch {
          return [];
        }
      });
      const results = await Promise.all(logPromises);
      const flattened: SyncLogItem[] = results.flat().sort((a, b) => 
        new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
      );
      setSyncLogs(flattened);
    } catch (err) {
      console.error('Failed to fetch sync logs', err);
    } finally {
      setLogsLoading(false);
    }
  };

  useEffect(() => {
    fetchIntegrations();
  }, []);

  const handleConnect = async (providerName: string, providerType: string) => {
    try {
      setNotice(null);
      await api.post('/integrations', {
        provider_name: providerName,
        provider_type: providerType,
        credentials: { method: 'MOCK_ENTERPRISE_API' },
      });
      setNotice({ type: 'success', text: `Successfully connected ${providerName.toUpperCase()}` });
      fetchIntegrations();
    } catch (err: any) {
      setNotice({ type: 'error', text: err?.response?.data?.detail || 'Failed to connect integration' });
    }
  };

  const handleTestConnection = async (id: string, name: string) => {
    try {
      setNotice(null);
      await api.post(`/integrations/${id}/test`);
      setNotice({ type: 'success', text: `Connection test succeeded for ${name}` });
    } catch (err: any) {
      setNotice({ type: 'error', text: err?.response?.data?.detail || `Connection test failed for ${name}` });
    }
  };

  const handleSync = async (id: string, providerName: string) => {
    try {
      setNotice(null);
      setSyncingProvider(providerName);
      setSyncModalOpen(true);
      setSyncResult(null);
      const res = await api.post(`/integrations/${id}/sync`);
      setSyncResult(res.data);
      fetchIntegrations();
    } catch (err: any) {
      setSyncResult({
        status: 'Failed',
        message: err?.response?.data?.detail || 'Data synchronization pipeline encountered an error'
      });
    }
  };

  const handleDisconnect = async (id: string, name: string) => {
    try {
      setNotice(null);
      await api.post(`/integrations/${id}/disconnect`);
      setNotice({ type: 'success', text: `Disconnected ${name}` });
      fetchIntegrations();
    } catch (err: any) {
      setNotice({ type: 'error', text: err?.response?.data?.detail || 'Failed to disconnect' });
    }
  };

  const erpIntegration = integrations.find(
    (i) => i.provider_name.toLowerCase() === 'demo_erp' || i.provider_type.toUpperCase() === 'DEMO_ERP' || i.provider_type.toUpperCase() === 'ERP'
  );

  const hrisIntegration = integrations.find(
    (i) => i.provider_name.toLowerCase() === 'demo_hris' || i.provider_type.toUpperCase() === 'DEMO_HRIS' || i.provider_type.toUpperCase() === 'HRIS'
  );

  if (loading) {
    return (
      <div className="p-8 max-w-7xl mx-auto space-y-6">
        <div className="skeleton h-8 w-64 rounded-xl" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => <div key={i} className="skeleton h-64 rounded-2xl" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-8 page-enter">
      {/* Page Header */}
      <div>
        <div className="flex items-center gap-3 mb-1">
          <div className="p-2 bg-indigo-50 dark:bg-indigo-900/30 rounded-xl">
            <Database className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Data Sources & Integrations</h1>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400 ml-12">
          Connect NeuroHR X to external enterprise ERP and HRIS systems through standardized API pipelines.
        </p>
      </div>

      {notice && (
        <div className={`p-4 rounded-xl text-xs font-semibold flex items-center justify-between ${
          notice.type === 'success' 
            ? 'bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300'
            : 'bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-300'
        }`}>
          <span>{notice.text}</span>
          <button onClick={() => setNotice(null)} className="text-xs opacity-75 hover:opacity-100">Dismiss</button>
        </div>
      )}

      {/* Integration Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Demo ERP Card */}
        <IntegrationCard
          title="Demo ERP"
          description="Simulates SAP, Oracle ERP, or Microsoft Dynamics for operational master workforce data."
          providerName="demo_erp"
          providerType="DEMO_ERP"
          integration={erpIntegration}
          onConnect={() => handleConnect('demo_erp', 'DEMO_ERP')}
          onTest={() => erpIntegration && handleTestConnection(erpIntegration.integration_id || erpIntegration.id, 'Demo ERP')}
          onSync={() => erpIntegration && handleSync(erpIntegration.integration_id || erpIntegration.id, 'Demo ERP')}
          onDisconnect={() => erpIntegration && handleDisconnect(erpIntegration.integration_id || erpIntegration.id, 'Demo ERP')}
        />
        
        {/* Demo HRIS Card */}
        <IntegrationCard
          title="Demo HRIS"
          description="Simulates Workday, BambooHR, or SuccessFactors for human capital and performance evaluations."
          providerName="demo_hris"
          providerType="DEMO_HRIS"
          integration={hrisIntegration}
          onConnect={() => handleConnect('demo_hris', 'DEMO_HRIS')}
          onTest={() => hrisIntegration && handleTestConnection(hrisIntegration.integration_id || hrisIntegration.id, 'Demo HRIS')}
          onSync={() => hrisIntegration && handleSync(hrisIntegration.integration_id || hrisIntegration.id, 'Demo HRIS')}
          onDisconnect={() => hrisIntegration && handleDisconnect(hrisIntegration.integration_id || hrisIntegration.id, 'Demo HRIS')}
        />

        {/* CSV Upload Card */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-6 flex flex-col justify-between shadow-xs card-hover">
          <div>
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-purple-50 dark:bg-purple-950/40 text-purple-600">
                  <FileSpreadsheet className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-gray-900 dark:text-white">CSV Workforce Import</h3>
                  <p className="text-[11px] text-gray-400 dark:text-gray-500 font-mono">FILE_IMPORT</p>
                </div>
              </div>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                Active
              </span>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed mb-5">
              Direct spreadsheet upload supporting batch ingestion with automatic column mapping and validation.
            </p>
            <div className="p-3 bg-gray-50 dark:bg-gray-700/40 rounded-xl mb-5 text-[11px]">
              <span className="text-gray-500 dark:text-gray-400 block mb-1">Standard Ingestion:</span>
              <span className="font-semibold text-gray-800 dark:text-gray-200">Manual / Periodic CSV Sync</span>
            </div>
          </div>
          <Link
            to="/dashboard/workforce/import"
            className="w-full py-2.5 bg-gray-900 hover:bg-black dark:bg-gray-700 dark:hover:bg-gray-600 text-white rounded-xl text-xs font-semibold transition flex items-center justify-center gap-1.5"
          >
            Launch CSV Importer
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Sync Logs Section */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-xs overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-gray-500" />
            <h2 className="text-base font-bold text-gray-900 dark:text-white">Integration Synchronization Audit Logs</h2>
          </div>
          <button
            onClick={() => fetchIntegrations()}
            className="text-xs text-indigo-600 dark:text-indigo-400 font-semibold hover:underline flex items-center gap-1"
          >
            <RefreshCw className={`w-3 h-3 ${logsLoading ? 'animate-spin' : ''}`} />
            Refresh Logs
          </button>
        </div>

        {syncLogs.length === 0 ? (
          <div className="p-8 text-center text-xs text-gray-400">
            No synchronization logs recorded yet. Trigger a sync using the cards above to see live pipeline execution telemetry.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-gray-50 dark:bg-gray-700/50 text-gray-500 uppercase font-semibold">
                <tr>
                  <th className="px-6 py-3 text-left">Integration</th>
                  <th className="px-6 py-3 text-left">Started At</th>
                  <th className="px-6 py-3 text-left">Status</th>
                  <th className="px-6 py-3 text-right">Extracted</th>
                  <th className="px-6 py-3 text-right">Created</th>
                  <th className="px-6 py-3 text-right">Updated</th>
                  <th className="px-6 py-3 text-right">Failed</th>
                  <th className="px-6 py-3 text-left">Result Summary</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {syncLogs.slice(0, 15).map((log) => {
                  const isSuccess = log.status === 'SUCCESS' || log.status === 'Success';
                  const isPartial = log.status === 'COMPLETED_WITH_ERRORS';
                  return (
                    <tr key={log.id} className="hover:bg-gray-50/50 dark:hover:bg-gray-700/30">
                      <td className="px-6 py-3 font-mono font-bold text-gray-800 dark:text-gray-200">
                        {log.integration_id}
                      </td>
                      <td className="px-6 py-3 text-gray-500">
                        {new Date(log.started_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-3">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-semibold ${
                          isSuccess
                            ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
                            : isPartial
                            ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
                            : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                        }`}>
                          {isSuccess ? <CheckCircle2 className="w-3 h-3" /> : isPartial ? <AlertTriangle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                          {log.status}
                        </span>
                      </td>
                      <td className="px-6 py-3 text-right font-mono font-bold text-gray-900 dark:text-white">
                        {log.records_fetched}
                      </td>
                      <td className="px-6 py-3 text-right font-mono font-bold text-emerald-600">
                        +{log.records_created}
                      </td>
                      <td className="px-6 py-3 text-right font-mono font-bold text-blue-600">
                        ↻ {log.records_updated}
                      </td>
                      <td className="px-6 py-3 text-right font-mono font-bold text-red-500">
                        {log.records_failed}
                      </td>
                      <td className="px-6 py-3 text-gray-600 dark:text-gray-300 max-w-xs truncate" title={log.message}>
                        {log.message || 'Complete'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
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
