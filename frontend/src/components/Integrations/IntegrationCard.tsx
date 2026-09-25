import React, { useState } from 'react';
import { Database, Play, RefreshCw, Unplug, Check } from 'lucide-react';

interface IntegrationCardProps {
  title: string;
  description: string;
  providerName: string;
  providerType: string;
  integration: any;
  onConnect: () => Promise<void> | void;
  onTest: () => Promise<void> | void;
  onSync: () => Promise<void> | void;
  onDisconnect: () => Promise<void> | void;
}

const IntegrationCard: React.FC<IntegrationCardProps> = ({
  title,
  description,
  integration,
  onConnect,
  onTest,
  onSync,
  onDisconnect,
}) => {
  const [testing, setTesting] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const isConnected = integration?.status?.toLowerCase() === 'connected';

  const handleTest = async () => {
    setTesting(true);
    try {
      await onTest();
    } finally {
      setTesting(false);
    }
  };

  const handleConnect = async () => {
    setConnecting(true);
    try {
      await onConnect();
    } finally {
      setConnecting(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-6 flex flex-col justify-between shadow-xs card-hover transition-all">
      <div>
        <div className="flex justify-between items-start mb-4">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-xl ${isConnected ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600' : 'bg-gray-100 dark:bg-gray-700 text-gray-500'}`}>
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-gray-900 dark:text-white">{title}</h3>
              <p className="text-[11px] text-gray-400 dark:text-gray-500 font-mono">
                {integration?.integration_id || 'Not provisioned'}
              </p>
            </div>
          </div>

          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${
            isConnected
              ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800'
              : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-gray-400'}`} />
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>

        <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed mb-5">
          {description}
        </p>
        
        <div className="p-3 bg-gray-50 dark:bg-gray-700/40 rounded-xl mb-5 text-[11px] space-y-1">
          <div className="flex justify-between text-gray-500 dark:text-gray-400">
            <span>Last Synced:</span>
            <span className="font-semibold text-gray-800 dark:text-gray-200">
              {integration?.last_sync_at ? new Date(integration.last_sync_at).toLocaleString() : 'Never'}
            </span>
          </div>
          <div className="flex justify-between text-gray-500 dark:text-gray-400">
            <span>Source Type:</span>
            <span className="font-semibold text-gray-800 dark:text-gray-200 uppercase">
              {integration?.provider_type || 'ENTERPRISE'}
            </span>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-2 pt-2 border-t border-gray-100 dark:border-gray-700">
        {!isConnected ? (
          <button
            onClick={handleConnect}
            disabled={connecting}
            className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs transition flex items-center justify-center gap-1.5 disabled:opacity-50"
          >
            {connecting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
            {connecting ? 'Connecting...' : 'Authorize & Connect'}
          </button>
        ) : (
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={handleTest}
                disabled={testing}
                className="py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-xl text-xs font-semibold transition flex items-center justify-center gap-1.5"
              >
                {testing ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3 text-emerald-500" />}
                {testing ? 'Testing...' : 'Test Link'}
              </button>
              <button
                onClick={onSync}
                className="py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs transition flex items-center justify-center gap-1.5"
              >
                <RefreshCw className="w-3 h-3" />
                Sync Now
              </button>
            </div>
            <button
              onClick={onDisconnect}
              className="w-full py-1.5 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 rounded-lg text-xs font-medium transition flex items-center justify-center gap-1.5"
            >
              <Unplug className="w-3.5 h-3.5" />
              Disconnect Integration
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default IntegrationCard;
