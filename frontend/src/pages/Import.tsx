import React, { useState } from 'react';
import axios from 'axios';
import { UploadCloud, CheckCircle, AlertCircle, FileText, X, Trash2, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface CSVPreviewData {
  fileName: string;
  fileSize: string;
  rowCount: number;
  columns: string[];
  rows: Record<string, string>[];
}

export default function Import() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<CSVPreviewData | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const [totalCount, setTotalCount] = useState<number | null>(null);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [clearMessage, setClearMessage] = useState('');
  const navigate = useNavigate();

  const fetchStats = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/v1/workforce/stats');
      setTotalCount(res.data.total_employees);
    } catch {
      // ignore
    }
  };

  React.useEffect(() => {
    fetchStats();
  }, []);

  const handleClearAllData = async () => {
    try {
      setIsProcessing(true);
      setError('');
      setClearMessage('');
      const res = await axios.delete('http://localhost:8000/api/v1/workforce/clear-data');
      setClearMessage(res.data.message || 'All workforce records wiped successfully.');
      setShowClearConfirm(false);
      setResult(null);
      setFile(null);
      setPreview(null);
      fetchStats();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to clear workforce data');
    } finally {
      setIsProcessing(false);
    }
  };

  const parseCSVClientSide = (fileContent: string, selectedFile: File) => {
    const lines = fileContent.split(/\r\n|\n/).filter(line => line.trim().length > 0);
    if (lines.length === 0) return;

    const headers = lines[0].split(',').map(h => h.trim().replace(/^["']|["']$/g, ''));
    const rows: Record<string, string>[] = [];

    // Preview first 5 rows
    const previewLineCount = Math.min(lines.length - 1, 5);
    for (let i = 1; i <= previewLineCount; i++) {
      const values = lines[i].split(',').map(v => v.trim().replace(/^["']|["']$/g, ''));
      const rowObj: Record<string, string> = {};
      headers.forEach((h, idx) => {
        rowObj[h] = values[idx] || '';
      });
      rows.push(rowObj);
    }

    const formatSize = (bytes: number) => {
      if (bytes < 1024) return `${bytes} bytes`;
      if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
      return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    setPreview({
      fileName: selectedFile.name,
      fileSize: formatSize(selectedFile.size),
      rowCount: lines.length - 1,
      columns: headers,
      rows: rows
    });
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selected = e.target.files[0];
      setFile(selected);
      setError('');
      setResult(null);

      const reader = new FileReader();
      reader.onload = (event) => {
        const text = event.target?.result as string;
        parseCSVClientSide(text, selected);
      };
      reader.readAsText(selected);
    }
  };

  const handleCancel = () => {
    setFile(null);
    setPreview(null);
    setError('');
    setResult(null);
  };

  const handleImport = async () => {
    if (!file) return;
    setIsProcessing(true);
    setStatusMessage('Uploading & Validating CSV data...');
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      setStatusMessage('Importing into database...');
      const response = await axios.post('http://localhost:8000/api/v1/workforce/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload and validate CSV');
    } finally {
      setIsProcessing(false);
      setStatusMessage('');
    }
  };

  const handleAnalyze = async () => {
    try {
      setIsProcessing(true);
      setStatusMessage('Running attrition model predictions...');
      await axios.post('http://localhost:8000/api/v1/attrition/predict-all');
      navigate('/dashboard/intelligence/attrition');
    } catch (err) {
      setError('Failed to run attrition analysis');
    } finally {
      setIsProcessing(false);
      setStatusMessage('');
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Import Workforce Data</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Upload employee CSV data</p>
      </div>

      <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-100 dark:bg-gray-800 dark:border-gray-700">
        {!result ? (
          <>
            {!preview ? (
              <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-12 text-center hover:border-indigo-500 transition-colors">
                <UploadCloud className="mx-auto h-16 w-16 text-indigo-500 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Drag & Drop CSV</h3>
                <p className="text-sm text-gray-500 mb-4">Or choose a file from your computer</p>
                <label
                  htmlFor="file-upload"
                  className="cursor-pointer inline-flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-md shadow-sm"
                >
                  <span>Choose CSV</span>
                  <input
                    id="file-upload"
                    name="file-upload"
                    type="file"
                    className="sr-only"
                    accept=".csv"
                    onChange={handleFileChange}
                  />
                </label>
              </div>
            ) : (
              <div className="space-y-6">
                {/* File Details Summary */}
                <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-lg border border-gray-200 dark:border-gray-600 flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <FileText className="w-8 h-8 text-indigo-500" />
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">{preview.fileName}</h4>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Size: <span className="font-medium text-gray-700 dark:text-gray-300">{preview.fileSize}</span> &middot; Rows: <span className="font-medium text-gray-700 dark:text-gray-300">{preview.rowCount}</span> &middot; Columns: <span className="font-medium text-gray-700 dark:text-gray-300">{preview.columns.length}</span>
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={handleCancel}
                    disabled={isProcessing}
                    className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-white"
                    title="Cancel selection"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {/* Detected Columns */}
                <div>
                  <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Detected Columns ({preview.columns.length})</h4>
                  <div className="flex flex-wrap gap-2">
                    {preview.columns.map((col, idx) => (
                      <span key={idx} className="px-2.5 py-1 bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 rounded text-xs font-medium border border-indigo-100 dark:border-indigo-800">
                        {col}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Preview Table */}
                <div>
                  <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Data Preview (First 5 Rows)</h4>
                  <div className="overflow-x-auto rounded-md border border-gray-200 dark:border-gray-700">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700 text-xs">
                      <thead className="bg-gray-100 dark:bg-gray-700">
                        <tr>
                          {preview.columns.map((col, idx) => (
                            <th key={idx} className="px-4 py-2 text-left font-semibold text-gray-700 dark:text-gray-200">{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                        {preview.rows.map((row, rIdx) => (
                          <tr key={rIdx}>
                            {preview.columns.map((col, cIdx) => (
                              <td key={cIdx} className="px-4 py-2 whitespace-nowrap text-gray-600 dark:text-gray-300">{row[col]}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center justify-end space-x-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <button
                    onClick={handleCancel}
                    disabled={isProcessing}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-600 disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleImport}
                    disabled={isProcessing}
                    className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md text-sm font-medium shadow-sm disabled:opacity-50 flex items-center"
                  >
                    {isProcessing ? (statusMessage || 'Importing...') : 'Import Data'}
                  </button>
                </div>
              </div>
            )}

            {error && (
              <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-md flex items-start dark:bg-red-900/20 dark:text-red-400">
                <AlertCircle className="w-5 h-5 mr-2 mt-0.5 flex-shrink-0" />
                <span className="text-sm">{error}</span>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-8">
            <CheckCircle className="mx-auto h-16 w-16 text-green-500" />
            <h3 className="mt-4 text-xl font-bold text-gray-900 dark:text-white">Import Complete</h3>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
              Total Rows: <span className="font-semibold">{result.total_rows}</span> &middot; Valid: <span className="font-semibold text-green-600">{result.valid_rows}</span> &middot; Imported: <span className="font-semibold text-indigo-600">{result.imported_rows}</span>
            </p>

            {result.errors && result.errors.length > 0 && (
              <div className="mt-6 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-md text-left text-xs">
                <p className="font-semibold text-amber-800 dark:text-amber-300 mb-2">{result.invalid_rows} Invalid Records Encountered:</p>
                <ul className="list-disc pl-5 max-h-36 overflow-y-auto space-y-1 text-amber-700 dark:text-amber-400">
                  {result.errors.map((errText: string, i: number) => (
                    <li key={i}>{errText}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="mt-8 flex justify-center space-x-4">
              <button
                onClick={() => navigate('/dashboard/workforce/employees')}
                className="px-5 py-2.5 bg-white border border-gray-300 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-600"
              >
                View Employees
              </button>
              <button
                onClick={handleAnalyze}
                disabled={isProcessing}
                className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md text-sm font-medium shadow-sm flex items-center disabled:opacity-50"
              >
                {isProcessing ? 'Analyzing...' : 'Run Attrition Analysis'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Workforce Data Management Card */}
      <div className="mt-8 bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-6 shadow-xs flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Trash2 className="w-4 h-4 text-red-500" />
            Workforce Data Lifecycle & Removal
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Current database state: <span className="font-semibold text-gray-800 dark:text-gray-200">{totalCount !== null ? `${totalCount} employees stored` : 'Loading...'}</span>.
            Need to start fresh or remove imported test records?
          </p>
          {clearMessage && (
            <p className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 mt-1">
              ✓ {clearMessage}
            </p>
          )}
        </div>
        <button
          onClick={() => setShowClearConfirm(true)}
          disabled={isProcessing || totalCount === 0}
          className="px-4 py-2 bg-red-50 hover:bg-red-100 dark:bg-red-950/30 dark:hover:bg-red-900/40 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800/50 rounded-xl text-xs font-semibold transition flex items-center gap-1.5 disabled:opacity-40"
        >
          <Trash2 className="w-3.5 h-3.5" />
          Wipe / Clear All Records
        </button>
      </div>

      {/* Confirmation Modal */}
      {showClearConfirm && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
          <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-2xl border border-gray-100 dark:border-gray-800 text-center">
            <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-950/50 text-red-600 dark:text-red-400 flex items-center justify-center mx-auto">
              <Trash2 className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-gray-900 dark:text-white">Wipe All Workforce Data?</h3>
            <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
              This action will permanently delete all {totalCount || 0} imported employee profiles and their associated attrition risk predictions. This cannot be undone.
            </p>
            <div className="flex gap-2 pt-2">
              <button
                onClick={() => setShowClearConfirm(false)}
                className="flex-1 py-2 text-xs font-semibold bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-xl hover:bg-gray-200 dark:hover:bg-gray-700 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleClearAllData}
                disabled={isProcessing}
                className="flex-1 py-2 text-xs font-semibold bg-red-600 hover:bg-red-700 text-white rounded-xl shadow-xs transition flex items-center justify-center gap-1"
              >
                {isProcessing ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : 'Confirm Wipe'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
