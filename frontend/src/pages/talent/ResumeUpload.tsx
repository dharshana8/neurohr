import { useState } from 'react';

import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Upload, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';


interface UploadItemStatus {
  file: File;
  status: 'pending' | 'uploading' | 'extracting' | 'parsing' | 'storing' | 'completed' | 'error';
  candidateId?: string;
  candidateName?: string;
  errorMessage?: string;
}

export default function ResumeUpload() {
  const navigate = useNavigate();
  const [items, setItems] = useState<UploadItemStatus[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const handleFileSelect = (files: FileList | null) => {
    if (!files) return;
    const newItems: UploadItemStatus[] = [];
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const ext = file.name.split('.').pop()?.toLowerCase();
      if (ext === 'pdf' || ext === 'docx') {
        newItems.push({ file, status: 'pending' });
      } else {
        alert(`File ${file.name} is not a PDF or DOCX file.`);
      }
    }
    setItems(prev => [...prev, ...newItems]);
  };

  const processUploads = async () => {
    if (items.length === 0 || isProcessing) return;
    setIsProcessing(true);

    for (let i = 0; i < items.length; i++) {
      if (items[i].status === 'completed') continue;

      // 1. Uploading
      setItems(prev => prev.map((item, idx) => idx === i ? { ...item, status: 'uploading' } : item));
      await new Promise(r => setTimeout(r, 300));

      // 2. Extracting text
      setItems(prev => prev.map((item, idx) => idx === i ? { ...item, status: 'extracting' } : item));
      await new Promise(r => setTimeout(r, 400));

      // 3. Parsing resume
      setItems(prev => prev.map((item, idx) => idx === i ? { ...item, status: 'parsing' } : item));
      await new Promise(r => setTimeout(r, 400));

      // 4. Storing candidate
      setItems(prev => prev.map((item, idx) => idx === i ? { ...item, status: 'storing' } : item));

      const formData = new FormData();
      formData.append('file', items[i].file);

      try {
        const res = await axios.post('http://localhost:8000/api/v1/recruitment/candidates/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        const cand = res.data;
        setItems(prev => prev.map((item, idx) => idx === i ? {
          ...item,
          status: 'completed',
          candidateId: cand.candidate_id,
          candidateName: cand.name
        } : item));
      } catch (err: any) {
        const msg = err.response?.data?.detail || 'Upload failed.';
        setItems(prev => prev.map((item, idx) => idx === i ? {
          ...item,
          status: 'error',
          errorMessage: msg
        } : item));
      }
    }
    setIsProcessing(false);
  };

  const getStatusBadge = (item: UploadItemStatus) => {
    switch (item.status) {
      case 'pending':
        return <span className="text-xs text-gray-400">Ready to upload</span>;
      case 'uploading':
        return <span className="text-xs text-indigo-600 dark:text-indigo-400 font-medium inline-flex items-center gap-1"><Loader2 className="w-3 h-3 animate-spin" /> Uploading file...</span>;
      case 'extracting':
        return <span className="text-xs text-indigo-600 dark:text-indigo-400 font-medium inline-flex items-center gap-1"><Loader2 className="w-3 h-3 animate-spin" /> Extracting text...</span>;
      case 'parsing':
        return <span className="text-xs text-purple-600 dark:text-purple-400 font-medium inline-flex items-center gap-1"><Loader2 className="w-3 h-3 animate-spin" /> Parsing resume & skills...</span>;
      case 'storing':
        return <span className="text-xs text-blue-600 dark:text-blue-400 font-medium inline-flex items-center gap-1"><Loader2 className="w-3 h-3 animate-spin" /> Storing candidate profile...</span>;
      case 'completed':
        return <span className="text-xs text-emerald-600 dark:text-emerald-400 font-semibold inline-flex items-center gap-1"><CheckCircle2 className="w-3.5 h-3.5" /> Completed</span>;
      case 'error':
        return <span className="text-xs text-red-600 dark:text-red-400 font-semibold inline-flex items-center gap-1"><AlertCircle className="w-3.5 h-3.5" /> {item.errorMessage}</span>;
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <button
          onClick={() => navigate('/dashboard/talent/candidates')}
          className="inline-flex items-center text-xs font-medium text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 mb-3 gap-1"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Candidates
        </button>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Upload className="w-7 h-7 text-indigo-600 dark:text-indigo-400" />
          Upload Candidate Resumes
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Upload PDF or DOCX resumes. The AI engine will extract candidate skills, experience, and education.
        </p>
      </div>

      {/* Process pipeline legend */}
      <div className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 flex flex-wrap items-center justify-between text-xs text-gray-500 gap-2">
        <span className="font-semibold text-gray-700 dark:text-gray-300">Parsing Pipeline:</span>
        <span>Resume Upload &rarr; Text Extraction &rarr; Resume Parsing &rarr; Profile Storage &rarr; Ready for Matching</span>
      </div>

      {/* Drop Zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={e => {
          e.preventDefault();
          setDragOver(false);
          handleFileSelect(e.dataTransfer.files);
        }}
        className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors ${
          dragOver
            ? 'border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/20'
            : 'border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-indigo-400'
        }`}
      >
        <FileText className="w-12 h-12 text-indigo-500 mx-auto mb-3" />
        <h3 className="text-base font-bold text-gray-900 dark:text-white">
          Drag & Drop PDF or DOCX files here
        </h3>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Supports multiple resume uploads (max 10MB per file)
        </p>

        <label className="mt-5 inline-flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold cursor-pointer shadow-sm gap-2">
          <Upload className="w-4 h-4" />
          Browse Files
          <input
            type="file"
            multiple
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            className="hidden"
            onChange={e => handleFileSelect(e.target.files)}
          />
        </label>
      </div>

      {/* Upload items queue */}
      {items.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-gray-900 dark:text-white">
              Selected Resumes ({items.length})
            </h3>
            <button
              onClick={processUploads}
              disabled={isProcessing || items.every(i => i.status === 'completed')}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-sm disabled:opacity-50 inline-flex items-center gap-2"
            >
              {isProcessing ? 'Processing Resumes...' : 'Start Parsing'}
            </button>
          </div>

          <div className="space-y-3">
            {items.map((item, idx) => (
              <div
                key={idx}
                className="p-4 rounded-lg bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 flex items-center justify-between gap-4"
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-indigo-500 shrink-0" />
                  <div>
                    <p className="text-xs font-bold text-gray-900 dark:text-white">{item.file.name}</p>
                    <p className="text-[11px] text-gray-400">{(item.file.size / 1024).toFixed(1)} KB</p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  {getStatusBadge(item)}
                  {item.candidateId && (
                    <button
                      onClick={() => navigate(`/dashboard/talent/candidates/${item.candidateId}`)}
                      className="px-2.5 py-1 text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 rounded"
                    >
                      View Profile
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
