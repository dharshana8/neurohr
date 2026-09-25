import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, RefreshCw, X } from 'lucide-react';

interface SyncProgressModalProps {
  provider: string | null;
  result: any;
  onClose: () => void;
}

const SyncProgressModal: React.FC<SyncProgressModalProps> = ({ provider, result, onClose }) => {
  const isSuccess = result?.status === 'SUCCESS' || result?.status === 'Success';
  const isPartial = result?.status === 'COMPLETED_WITH_ERRORS';

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-xs flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-100 dark:border-gray-800 max-w-md w-full p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-gray-100 dark:border-gray-800">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-gray-900 dark:text-white">{provider} Data Sync</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {!result ? (
          <div className="flex flex-col items-center justify-center py-10 space-y-3">
            <RefreshCw className="w-10 h-10 text-indigo-600 dark:text-indigo-400 animate-spin" />
            <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">Synchronizing records...</p>
            <p className="text-xs text-gray-400">Extracting, normalizing, and upserting data</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className={`p-4 rounded-xl border flex items-start gap-3 ${
              isSuccess 
                ? 'bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-800/50 text-emerald-800 dark:text-emerald-300'
                : isPartial
                ? 'bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800/50 text-amber-800 dark:text-amber-300'
                : 'bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-800/50 text-red-800 dark:text-red-300'
            }`}>
              {isSuccess ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 flex-shrink-0 mt-0.5" />
              ) : isPartial ? (
                <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
              ) : (
                <XCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              )}
              <div>
                <p className="font-bold text-sm">{result.status}</p>
                <p className="text-xs mt-0.5 opacity-90">{result.message || 'Operation completed.'}</p>
              </div>
            </div>

            {(isSuccess || isPartial || result.records_fetched !== undefined) && (
              <div className="bg-gray-50 dark:bg-gray-800/60 rounded-xl p-4 space-y-2.5 text-xs">
                <div className="flex justify-between items-center text-gray-600 dark:text-gray-400">
                  <span>Records Extracted:</span>
                  <span className="font-mono font-bold text-gray-900 dark:text-white">{result.records_fetched || 0}</span>
                </div>
                <div className="flex justify-between items-center text-gray-600 dark:text-gray-400">
                  <span>New Employees Created:</span>
                  <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">+{result.records_created || 0}</span>
                </div>
                <div className="flex justify-between items-center text-gray-600 dark:text-gray-400">
                  <span>Existing Profiles Updated:</span>
                  <span className="font-mono font-bold text-blue-600 dark:text-blue-400">↻ {result.records_updated || 0}</span>
                </div>
                <div className="flex justify-between items-center text-gray-600 dark:text-gray-400">
                  <span>Validation Failures:</span>
                  <span className={`font-mono font-bold ${result.records_failed ? 'text-red-600 dark:text-red-400' : 'text-gray-400'}`}>
                    {result.records_failed || 0}
                  </span>
                </div>
              </div>
            )}

            <button
              onClick={onClose}
              className="w-full py-2.5 bg-gray-900 hover:bg-black dark:bg-gray-800 dark:hover:bg-gray-700 text-white rounded-xl text-xs font-semibold transition"
            >
              Done
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default SyncProgressModal;
