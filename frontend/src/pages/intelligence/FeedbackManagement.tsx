import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';
import {
  Plus, Search, RefreshCw,
  Upload, Trash2, Edit, ChevronLeft, ChevronRight,
  Smile, Meh, Frown, CheckCircle, AlertCircle, X,
  ArrowLeft
} from 'lucide-react';

interface SentimentResult {
  sentiment_id: string;
  feedback_id: string;
  employee_id?: string;
  sentiment: string;
  sentiment_score: {
    positive: number;
    neutral: number;
    negative: number;
    compound: number;
  };
  model_name: string;
  model_version: string;
  analyzed_at: string;
}

interface FeedbackItem {
  id: string;
  feedback_id: string;
  employee_id?: string;
  department: string;
  category: string;
  feedback_text: string;
  source: string;
  submitted_at: string;
  is_synthetic: boolean;
  sentiment_result?: SentimentResult;
  created_at: string;
  updated_at: string;
}

export default function FeedbackManagement() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const isManagerOrAdmin = user?.role === 'ORGANIZATION_ADMIN' || user?.role === 'HR_MANAGER';

  const [feedbacks, setFeedbacks] = useState<FeedbackItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(15);
  const [loading, setLoading] = useState(true);

  // Filters & Search
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [selectedDept, setSelectedDept] = useState('ALL');
  const [selectedSentiment, setSelectedSentiment] = useState('ALL');

  // Modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showClearAllModal, setShowClearAllModal] = useState(false);
  const [clearingAll, setClearingAll] = useState(false);
  const [selectedFeedback, setSelectedFeedback] = useState<FeedbackItem | null>(null);

  // Form State
  const [formData, setFormData] = useState({
    department: 'Engineering',
    category: 'WORKLOAD',
    source: 'SURVEY',
    feedback_text: '',
    employee_id: ''
  });

  // Import State
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<string | null>(null);

  // Action status
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const handleClearAllFeedback = async () => {
    setClearingAll(true);
    try {
      await api.delete('/feedback/actions/clear-all');
      setShowClearAllModal(false);
      fetchFeedbacks();
    } catch (err) {
      console.error('Failed to clear all feedback', err);
    } finally {
      setClearingAll(false);
    }
  };

  useEffect(() => {
    fetchFeedbacks();
  }, [page, search, selectedCategory, selectedDept, selectedSentiment]);

  const fetchFeedbacks = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
        category: selectedCategory,
        department: selectedDept,
        sentiment: selectedSentiment
      });
      if (search.trim()) {
        params.append('search', search.trim());
      }

      const res = await api.get(`/feedback?${params.toString()}`);
      setFeedbacks(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error('Failed to load feedback records', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.feedback_text.trim()) return;

    try {
      await api.post('/feedback', {
        ...formData,
        employee_id: formData.employee_id.trim() || null
      });
      setShowAddModal(false);
      setFormData({
        department: 'Engineering',
        category: 'WORKLOAD',
        source: 'SURVEY',
        feedback_text: '',
        employee_id: ''
      });
      fetchFeedbacks();
    } catch (err) {
      console.error('Failed to create feedback', err);
    }
  };

  const handleEditFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFeedback) return;

    try {
      await api.put(`/feedback/${selectedFeedback.feedback_id}`, {
        department: formData.department,
        category: formData.category,
        source: formData.source,
        feedback_text: formData.feedback_text,
        employee_id: formData.employee_id.trim() || null
      });
      setShowEditModal(false);
      setSelectedFeedback(null);
      fetchFeedbacks();
    } catch (err) {
      console.error('Failed to update feedback', err);
    }
  };

  const handleDeleteFeedback = async () => {
    if (!selectedFeedback) return;

    try {
      await api.delete(`/feedback/${selectedFeedback.feedback_id}`);
      setShowDeleteModal(false);
      setSelectedFeedback(null);
      fetchFeedbacks();
    } catch (err) {
      console.error('Failed to delete feedback', err);
    }
  };

  const handleAnalyzeRow = async (feedbackId: string) => {
    setActionLoading(feedbackId);
    try {
      await api.post(`/sentiment/analyze/${feedbackId}`);
      await fetchFeedbacks();
    } catch (err) {
      console.error('Single analysis failed', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleImportCSV = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!importFile) return;

    setImporting(true);
    setImportResult(null);

    const formDataUpload = new FormData();
    formDataUpload.append('file', importFile);

    try {
      const res = await api.post('/feedback/import', formDataUpload);
      setImportResult(`Successfully imported ${res.data.imported_count} records from ${res.data.total_rows} rows.`);
      setImportFile(null);
      fetchFeedbacks();
    } catch (err: any) {
      setImportResult(err.response?.data?.detail || 'Import failed. Please check CSV format.');
    } finally {
      setImporting(false);
    }
  };

  const openEditModal = (fb: FeedbackItem) => {
    setSelectedFeedback(fb);
    setFormData({
      department: fb.department,
      category: fb.category,
      source: fb.source,
      feedback_text: fb.feedback_text,
      employee_id: fb.employee_id || ''
    });
    setShowEditModal(true);
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <button
            onClick={() => navigate('/dashboard/intelligence/sentiment')}
            className="flex items-center gap-1.5 text-xs font-semibold text-indigo-400 hover:text-indigo-300 mb-2 transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Sentiment Overview
          </button>
          <h1 className="text-2xl font-bold text-white tracking-tight">Workplace Feedback Management</h1>
          <p className="text-sm text-slate-400">
            Maintain, import, and classify authorized employee feedback and surveys
          </p>
        </div>

        <div className="flex items-center flex-wrap gap-3">
          {isManagerOrAdmin && (
            <>
              {total > 0 && (
                <button
                  onClick={() => setShowClearAllModal(true)}
                  className="px-4 py-2 text-sm font-medium text-rose-300 bg-rose-950/40 hover:bg-rose-900/50 rounded-lg border border-rose-800/60 transition flex items-center gap-2"
                >
                  <Trash2 className="w-4 h-4 text-rose-400" />
                  Clear All Feedback
                </button>
              )}

              <button
                onClick={() => {
                  setImportResult(null);
                  setImportFile(null);
                  setShowImportModal(true);
                }}
                className="px-4 py-2 text-sm font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 transition flex items-center gap-2"
              >
                <Upload className="w-4 h-4 text-slate-400" />
                Import CSV
              </button>

              <button
                onClick={() => setShowAddModal(true)}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg shadow-lg shadow-indigo-500/20 transition flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Add Feedback
              </button>
            </>
          )}
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-slate-900/60 backdrop-blur-sm border border-slate-800 p-4 rounded-xl flex flex-wrap items-center justify-between gap-4">
        {/* Search */}
        <div className="relative min-w-[260px] flex-1 max-w-md">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search feedback text, department, employee..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-9 pr-3.5 py-1.5 text-xs text-white placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>

        {/* Dropdown Filters */}
        <div className="flex items-center flex-wrap gap-3">
          <select
            value={selectedDept}
            onChange={(e) => {
              setSelectedDept(e.target.value);
              setPage(1);
            }}
            className="bg-slate-800 text-slate-200 border border-slate-700 rounded-lg px-3 py-1.5 text-xs focus:ring-1 focus:ring-indigo-500 focus:outline-none"
          >
            <option value="ALL">All Departments</option>
            <option value="Engineering">Engineering</option>
            <option value="Product">Product</option>
            <option value="Sales">Sales</option>
            <option value="Marketing">Marketing</option>
            <option value="HR">HR</option>
            <option value="Customer Support">Customer Support</option>
            <option value="Finance">Finance</option>
            <option value="Operations">Operations</option>
          </select>

          <select
            value={selectedCategory}
            onChange={(e) => {
              setSelectedCategory(e.target.value);
              setPage(1);
            }}
            className="bg-slate-800 text-slate-200 border border-slate-700 rounded-lg px-3 py-1.5 text-xs focus:ring-1 focus:ring-indigo-500 focus:outline-none"
          >
            <option value="ALL">All Categories</option>
            <option value="ENGAGEMENT">Engagement</option>
            <option value="WORKPLACE">Workplace</option>
            <option value="MANAGEMENT">Management</option>
            <option value="CULTURE">Culture</option>
            <option value="WORKLOAD">Workload</option>
            <option value="CAREER">Career</option>
            <option value="BENEFITS">Benefits</option>
            <option value="EXIT">Exit</option>
          </select>

          <select
            value={selectedSentiment}
            onChange={(e) => {
              setSelectedSentiment(e.target.value);
              setPage(1);
            }}
            className="bg-slate-800 text-slate-200 border border-slate-700 rounded-lg px-3 py-1.5 text-xs focus:ring-1 focus:ring-indigo-500 focus:outline-none"
          >
            <option value="ALL">All Sentiments</option>
            <option value="POSITIVE">Positive</option>
            <option value="NEUTRAL">Neutral</option>
            <option value="NEGATIVE">Negative</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/60 text-slate-400 font-semibold uppercase tracking-wider text-[10px] border-b border-slate-800">
              <tr>
                <th className="py-3.5 px-4">Department / Category</th>
                <th className="py-3.5 px-4">Feedback Content</th>
                <th className="py-3.5 px-4">Source</th>
                <th className="py-3.5 px-4">Submitted</th>
                <th className="py-3.5 px-4">Sentiment</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto text-indigo-400 mb-2" />
                    Loading feedback entries...
                  </td>
                </tr>
              ) : feedbacks.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    No feedback records match the current filters.
                  </td>
                </tr>
              ) : (
                feedbacks.map((fb) => {
                  const sent = fb.sentiment_result?.sentiment;
                  return (
                    <tr key={fb.feedback_id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <div className="font-medium text-white">{fb.department}</div>
                        <div className="text-[10px] text-indigo-400 font-semibold">{fb.category}</div>
                      </td>

                      <td className="py-3.5 px-4 max-w-md">
                        <p className="line-clamp-2 text-slate-300 leading-snug">
                          {fb.feedback_text}
                        </p>
                        {fb.employee_id && (
                          <span className="text-[10px] text-slate-500 mt-1 inline-block">
                            Employee: {fb.employee_id}
                          </span>
                        )}
                      </td>

                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[10px] font-medium">
                          {fb.source}
                        </span>
                      </td>

                      <td className="py-3.5 px-4 whitespace-nowrap text-slate-400">
                        {new Date(fb.submitted_at).toLocaleDateString()}
                      </td>

                      <td className="py-3.5 px-4 whitespace-nowrap">
                        {sent === 'POSITIVE' && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            <Smile className="w-3.5 h-3.5" /> Positive
                          </span>
                        )}
                        {sent === 'NEUTRAL' && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                            <Meh className="w-3.5 h-3.5" /> Neutral
                          </span>
                        )}
                        {sent === 'NEGATIVE' && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                            <Frown className="w-3.5 h-3.5" /> Negative
                          </span>
                        )}
                        {!sent && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-400 border border-slate-700">
                            Pending
                          </span>
                        )}
                      </td>

                      <td className="py-3.5 px-4 whitespace-nowrap text-right space-x-1">
                        <button
                          onClick={() => navigate(`/dashboard/intelligence/sentiment/${fb.feedback_id}`)}
                          className="px-2.5 py-1 text-[11px] text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded border border-slate-700 transition"
                        >
                          View
                        </button>

                        <button
                          onClick={() => handleAnalyzeRow(fb.feedback_id)}
                          disabled={actionLoading === fb.feedback_id}
                          className="px-2.5 py-1 text-[11px] text-indigo-300 hover:text-indigo-200 bg-indigo-900/30 hover:bg-indigo-900/50 rounded border border-indigo-700/40 transition"
                          title="Re-analyze sentiment"
                        >
                          <RefreshCw className={`w-3 h-3 inline ${actionLoading === fb.feedback_id ? 'animate-spin' : ''}`} />
                        </button>

                        {isManagerOrAdmin && (
                          <>
                            <button
                              onClick={() => openEditModal(fb)}
                              className="px-2.5 py-1 text-[11px] text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded border border-slate-700 transition"
                            >
                              <Edit className="w-3 h-3 inline" />
                            </button>

                            <button
                              onClick={() => {
                                setSelectedFeedback(fb);
                                setShowDeleteModal(true);
                              }}
                              className="px-2.5 py-1 text-[11px] text-rose-400 hover:text-rose-300 bg-rose-900/20 hover:bg-rose-900/40 rounded border border-rose-800/30 transition"
                            >
                              <Trash2 className="w-3 h-3 inline" />
                            </button>
                          </>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {total > limit && (
          <div className="p-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <div>
              Showing {(page - 1) * limit + 1} to {Math.min(page * limit, total)} of {total} records
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                disabled={page === 1}
                className="p-1.5 rounded-lg bg-slate-800 border border-slate-700 disabled:opacity-40"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="font-semibold text-slate-200">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                disabled={page === totalPages}
                className="p-1.5 rounded-lg bg-slate-800 border border-slate-700 disabled:opacity-40"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Add Feedback Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-base">Add Employee Feedback</h3>
              <button onClick={() => setShowAddModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateFeedback} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Department</label>
                  <select
                    value={formData.department}
                    onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="Engineering">Engineering</option>
                    <option value="Product">Product</option>
                    <option value="Sales">Sales</option>
                    <option value="Marketing">Marketing</option>
                    <option value="HR">HR</option>
                    <option value="Customer Support">Customer Support</option>
                    <option value="Finance">Finance</option>
                    <option value="Operations">Operations</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Category</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="ENGAGEMENT">Engagement</option>
                    <option value="WORKPLACE">Workplace</option>
                    <option value="MANAGEMENT">Management</option>
                    <option value="CULTURE">Culture</option>
                    <option value="WORKLOAD">Workload</option>
                    <option value="CAREER">Career</option>
                    <option value="BENEFITS">Benefits</option>
                    <option value="EXIT">Exit</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Source</label>
                  <select
                    value={formData.source}
                    onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="SURVEY">HR Survey</option>
                    <option value="HR_FORM">HR Feedback Form</option>
                    <option value="MANAGER_FEEDBACK">Manager Feedback</option>
                    <option value="EXIT_FEEDBACK">Exit Interview</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Employee ID (Optional)</label>
                  <input
                    type="text"
                    placeholder="e.g. EMP-101"
                    value={formData.employee_id}
                    onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Feedback Content</label>
                <textarea
                  rows={4}
                  placeholder="Enter employee feedback or survey response..."
                  value={formData.feedback_text}
                  onChange={(e) => setFormData({ ...formData, feedback_text: e.target.value })}
                  required
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium shadow-lg shadow-indigo-500/20"
                >
                  Save & Analyze
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Feedback Modal */}
      {showEditModal && selectedFeedback && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-base">Edit Employee Feedback</h3>
              <button onClick={() => setShowEditModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleEditFeedback} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Department</label>
                  <select
                    value={formData.department}
                    onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="Engineering">Engineering</option>
                    <option value="Product">Product</option>
                    <option value="Sales">Sales</option>
                    <option value="Marketing">Marketing</option>
                    <option value="HR">HR</option>
                    <option value="Customer Support">Customer Support</option>
                    <option value="Finance">Finance</option>
                    <option value="Operations">Operations</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Category</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="ENGAGEMENT">Engagement</option>
                    <option value="WORKPLACE">Workplace</option>
                    <option value="MANAGEMENT">Management</option>
                    <option value="CULTURE">Culture</option>
                    <option value="WORKLOAD">Workload</option>
                    <option value="CAREER">Career</option>
                    <option value="BENEFITS">Benefits</option>
                    <option value="EXIT">Exit</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Feedback Content</label>
                <textarea
                  rows={4}
                  value={formData.feedback_text}
                  onChange={(e) => setFormData({ ...formData, feedback_text: e.target.value })}
                  required
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowEditModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium shadow-lg shadow-indigo-500/20"
                >
                  Update & Re-Analyze
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Feedback Confirmation Modal */}
      {showDeleteModal && selectedFeedback && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center gap-3 text-rose-400">
              <AlertCircle className="w-6 h-6" />
              <h3 className="font-bold text-white text-base">Delete Feedback Record</h3>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Are you sure you want to permanently remove this feedback item and its sentiment scores?
              This action will be recorded in the tenant audit log.
            </p>
            <div className="flex justify-end gap-3 pt-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="px-4 py-2 text-xs rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700 font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteFeedback}
                className="px-4 py-2 text-xs rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-medium shadow-lg shadow-rose-600/20"
              >
                Confirm Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CSV Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Upload className="w-5 h-5 text-indigo-400" />
                <h3 className="font-bold text-white text-base">Import Feedback Dataset</h3>
              </div>
              <button onClick={() => setShowImportModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-400">
              Upload an authorized feedback CSV file containing: <br />
              <code className="text-indigo-300 bg-slate-800 px-1.5 py-0.5 rounded text-[11px]">
                feedback_id, employee_id, department, category, feedback_text, source, submitted_at
              </code>
            </p>

            <form onSubmit={handleImportCSV} className="space-y-4">
              <div className="border-2 border-dashed border-slate-700 hover:border-indigo-500/50 rounded-xl p-6 text-center transition">
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                  className="hidden"
                  id="csv-upload-input"
                />
                <label htmlFor="csv-upload-input" className="cursor-pointer space-y-2 block">
                  <div className="w-10 h-10 bg-indigo-500/10 text-indigo-400 rounded-xl flex items-center justify-center mx-auto">
                    <Upload className="w-5 h-5" />
                  </div>
                  <div className="text-xs font-semibold text-slate-300">
                    {importFile ? importFile.name : 'Select CSV file or drag here'}
                  </div>
                  <div className="text-[11px] text-slate-500">Only .csv files supported</div>
                </label>
              </div>

              {importResult && (
                <div className="p-3 rounded-lg bg-slate-800 border border-slate-700 text-xs text-slate-300 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  <span>{importResult}</span>
                </div>
              )}

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowImportModal(false)}
                  className="px-4 py-2 text-xs rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700 font-medium"
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={!importFile || importing}
                  className="px-4 py-2 text-xs rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium shadow-lg shadow-indigo-500/20"
                >
                  {importing ? 'Processing...' : 'Upload & Analyze'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Clear All Feedback Modal */}
      {showClearAllModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-900 border border-rose-800/80 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400 shrink-0">
                <Trash2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Clear All Workplace Feedback</h3>
                <p className="text-xs text-rose-400">Irreversible tenant purge</p>
              </div>
            </div>

            <p className="text-sm text-slate-300">
              Are you sure you want to permanently delete <strong className="text-white">all {total} feedback records</strong> and their corresponding sentiment intelligence analytics?
            </p>
            <div className="p-3 bg-rose-950/40 rounded-xl text-xs text-rose-300 border border-rose-900/50 space-y-1">
              <p className="font-semibold">⚠️ What will happen:</p>
              <ul className="list-disc list-inside space-y-0.5 text-slate-400">
                <li>All employee feedback surveys and comments will be wiped</li>
                <li>All calculated VADER/hybrid sentiment results will be erased</li>
                <li>Department sentiment scores and trend charts will be reset</li>
              </ul>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowClearAllModal(false)}
                disabled={clearingAll}
                className="px-4 py-2 text-xs rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700 font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleClearAllFeedback}
                disabled={clearingAll}
                className="px-4 py-2 text-xs rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-medium shadow-lg shadow-rose-600/20 transition-colors disabled:opacity-50"
              >
                {clearingAll ? 'Clearing All...' : 'Yes, Delete Everything'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
