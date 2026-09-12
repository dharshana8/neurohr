import React from 'react';

interface IntegrationCardProps {
  title: string;
  description: string;
  providerName: string;
  providerType: string;
  integration: any;
  onConnect: () => void;
  onTest: () => void;
  onSync: () => void;
  onDisconnect: () => void;
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
  const isConnected = integration?.status === 'Connected';

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col justify-between h-full">
      <div>
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-xl font-semibold">{title}</h3>
          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${isConnected ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
        <p className="text-gray-500 mb-6">{description}</p>
        
        {isConnected && (
          <div className="text-sm text-gray-500 mb-6">
            Last sync: {integration.last_sync_at ? new Date(integration.last_sync_at).toLocaleString() : 'Never'}
          </div>
        )}
      </div>

      <div className="flex flex-col gap-2 mt-auto">
        {!isConnected ? (
          <button
            onClick={onConnect}
            className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
          >
            Authorize
          </button>
        ) : (
          <>
            <button
              onClick={onTest}
              className="w-full bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 transition"
            >
              Test Connection
            </button>
            <button
              onClick={onSync}
              className="w-full bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition"
            >
              Sync Now
            </button>
            <button
              onClick={onDisconnect}
              className="w-full text-red-600 bg-red-50 px-4 py-2 rounded-lg hover:bg-red-100 transition mt-2"
            >
              Disconnect
            </button>
          </>
        )}
      </div>
    </div>
  );
};

export default IntegrationCard;
