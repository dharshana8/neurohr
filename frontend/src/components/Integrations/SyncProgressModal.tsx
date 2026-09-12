import React from 'react';

interface SyncProgressModalProps {
  provider: string | null;
  result: any;
  onClose: () => void;
}

const SyncProgressModal: React.FC<SyncProgressModalProps> = ({ provider, result, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
        <h2 className="text-2xl font-bold mb-4">{provider} Sync</h2>
        
        {!result ? (
          <div className="flex flex-col items-center justify-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
            <p className="text-gray-600">Syncing data...</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className={`p-4 rounded-lg ${result.status === 'Success' ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'} border`}>
              <p className="font-semibold">{result.status}</p>
              <p className="text-sm mt-1">{result.message}</p>
            </div>
            
            {result.status === 'Success' && (
              <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">Records Fetched:</span>
                  <span className="font-semibold">{result.records_fetched}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Records Created:</span>
                  <span className="font-semibold text-green-600">{result.records_created}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Records Updated:</span>
                  <span className="font-semibold text-blue-600">{result.records_updated}</span>
                </div>
              </div>
            )}
            
            <button
              onClick={onClose}
              className="w-full bg-gray-900 text-white px-4 py-2 rounded-lg hover:bg-gray-800 transition mt-4"
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default SyncProgressModal;
