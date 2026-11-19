import { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Calendar, CheckCircle, Clock, FileText, AlertCircle, ShieldAlert,
  Send, Users, DollarSign, Check, X, Sparkles, Filter, ChevronRight
} from 'lucide-react';

interface LeaveRequest {
  id: string;
  employee_id: string;
  employee_name: string;
  department: string;
  leave_type: string;
  start_date: string;
  end_date: string;
  days: number;
  reason: string;
  status: string;
  ai_recommendation?: {
    verdict: string;
    confidence: number;
    project_impact: string;
    policy_compliant: boolean;
  };
}

interface Grievance {
  id: string;
  employee_name: string;
  category: string;
  subject: string;
  details: string;
  status: string;
  ai_analysis?: {
    urgency: string;
    sentiment_score: number;
    flight_risk_impact: string;
    recommended_action: string;
  };
}

export default function HRISPortal() {
  const [activeTab, setActiveTab] = useState<'leaves' | 'grievances' | 'attendance' | 'payroll'>('leaves');
  const [leaves, setLeaves] = useState<LeaveRequest[]>([]);
  const [grievances, setGrievances] = useState<Grievance[]>([]);
  const [attendance, setAttendance] = useState<any>(null);
  const [payroll, setPayroll] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Leave Form modal state
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [leaveType, setLeaveType] = useState('Casual Leave');
  const [startDate, setStartDate] = useState('2026-11-10');
  const [endDate, setEndDate] = useState('2026-11-12');
  const [reason, setReason] = useState('');
  const [applying, setApplying] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const fetchData = async () => {
    setLoading(false);
    try {
      const headers = getAuthHeaders();
      const [lRes, gRes, aRes, pRes] = await Promise.all([
        axios.get('http://localhost:8000/api/v1/hris/leaves', { headers }).catch(() => ({ data: [] })),
        axios.get('http://localhost:8000/api/v1/hris/grievances', { headers }).catch(() => ({ data: [] })),
        axios.get('http://localhost:8000/api/v1/hris/attendance/summary', { headers }).catch(() => ({ data: null })),
        axios.get('http://localhost:8000/api/v1/hris/payroll/overview', { headers }).catch(() => ({ data: null }))
      ]);
      setLeaves(Array.isArray(lRes.data) ? lRes.data : []);
      setGrievances(Array.isArray(gRes.data) ? gRes.data : []);
      setAttendance(aRes.data);
      setPayroll(pRes.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleUpdateLeaveStatus = async (leaveId: string, status: 'APPROVED' | 'REJECTED') => {
    try {
      await axios.put(`http://localhost:8000/api/v1/hris/leaves/${leaveId}/status?new_status=${status}`, {}, { headers: getAuthHeaders() });
      setLeaves(prev => prev.map(l => l.id === leaveId ? { ...l, status } : l));
    } catch (e) {
      console.error(e);
    }
  };

  const handleApplyLeave = async (e: React.FormEvent) => {
    e.preventDefault();
    setApplying(true);
    try {
      const res = await axios.post('http://localhost:8000/api/v1/hris/leaves', {
        employee_id: 'EMP-101',
        leave_type: leaveType,
        start_date: startDate,
        end_date: endDate,
        days: 3,
        reason: reason || 'Personal appointment'
      });
      setLeaves(prev => [res.data, ...prev]);
      setShowApplyModal(false);
      setReason('');
    } catch (err) {
      console.error(err);
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 text-xs font-semibold uppercase tracking-wider mb-2">
            🏢 Human Resource Information System
          </div>
          <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight">
            HRIS People & Operations Portal
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Empowering workforce self-service, AI-assisted leave resolution, employee grievances, and compensation.
          </p>
        </div>

        <button
          onClick={() => setShowApplyModal(true)}
          className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-semibold shadow-md shadow-indigo-500/25 transition-all"
        >
          <Calendar className="w-4 h-4" />
          Apply For Leave
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 dark:border-gray-800 gap-6">
        <button
          onClick={() => setActiveTab('leaves')}
          className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${
            activeTab === 'leaves'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-gray-200'
          }`}
        >
          <Calendar className="w-4 h-4" />
          Leave Requests & AI Approvals ({leaves.length})
        </button>
        <button
          onClick={() => setActiveTab('grievances')}
          className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${
            activeTab === 'grievances'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-gray-200'
          }`}
        >
          <ShieldAlert className="w-4 h-4" />
          Grievance Triage & Care ({grievances.length})
        </button>
        <button
          onClick={() => setActiveTab('attendance')}
          className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${
            activeTab === 'attendance'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-gray-200'
          }`}
        >
          <Clock className="w-4 h-4" />
          Attendance & Shift Clock
        </button>
        <button
          onClick={() => setActiveTab('payroll')}
          className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${
            activeTab === 'payroll'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-gray-200'
          }`}
        >
          <DollarSign className="w-4 h-4" />
          Payroll & Benefits
        </button>
      </div>

      {/* Content based on active tab */}
      {activeTab === 'leaves' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white dark:bg-gray-800 p-5 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm">
              <span className="text-xs font-semibold text-gray-400 uppercase">Pending Review</span>
              <p className="text-2xl font-bold text-amber-500 mt-1">
                {leaves.filter(l => l.status === 'PENDING_APPROVAL').length} Requests
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 p-5 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm">
              <span className="text-xs font-semibold text-gray-400 uppercase">Approved This Month</span>
              <p className="text-2xl font-bold text-emerald-500 mt-1">
                {leaves.filter(l => l.status === 'APPROVED').length} Granted
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 p-5 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm">
              <span className="text-xs font-semibold text-gray-400 uppercase">AI Recommendation Accuracy</span>
              <p className="text-2xl font-bold text-indigo-500 mt-1">98.4%</p>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center">
              <h2 className="font-bold text-gray-900 dark:text-white">Active Leave Petitions</h2>
              <span className="text-xs text-gray-500">Cross-referenced against ERP project dependencies</span>
            </div>

            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {leaves.map((leave) => (
                <div key={leave.id} className="p-6 hover:bg-gray-50/50 dark:hover:bg-gray-800/50 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-1.5 flex-1">
                    <div className="flex items-center gap-3">
                      <span className="font-semibold text-gray-900 dark:text-white text-base">
                        {leave.employee_name}
                      </span>
                      <span className="text-xs px-2.5 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 font-medium text-gray-600 dark:text-gray-300">
                        {leave.department}
                      </span>
                      <span className={`text-xs px-2.5 py-0.5 rounded-full font-semibold ${
                        leave.status === 'APPROVED' ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600' :
                        leave.status === 'REJECTED' ? 'bg-red-100 dark:bg-red-900/30 text-red-600' :
                        'bg-amber-100 dark:bg-amber-900/30 text-amber-600'
                      }`}>
                        {leave.status}
                      </span>
                    </div>

                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      <strong>{leave.leave_type}</strong> &bull; {leave.start_date} to {leave.end_date} ({leave.days} Days) &bull; <em>"{leave.reason}"</em>
                    </p>

                    {/* AI Autonomous Officer Insights */}
                    {leave.ai_recommendation && (
                      <div className="mt-2 p-3 rounded-xl bg-indigo-50/70 dark:bg-indigo-950/40 border border-indigo-100 dark:border-indigo-900/50 text-xs space-y-1 text-indigo-900 dark:text-indigo-200">
                        <div className="flex items-center gap-1.5 font-bold text-indigo-700 dark:text-indigo-400">
                          <Sparkles className="w-3.5 h-3.5" />
                          <span>Autonomous HR Recommendation: {leave.ai_recommendation.verdict}</span>
                          <span className="ml-auto text-[10px] bg-indigo-200/60 dark:bg-indigo-800/60 px-2 py-0.5 rounded-md">
                            Confidence: {(leave.ai_recommendation.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                        <p className="text-gray-700 dark:text-gray-300">
                          {leave.ai_recommendation.project_impact}
                        </p>
                      </div>
                    )}
                  </div>

                  {leave.status === 'PENDING_APPROVAL' && (
                    <div className="flex items-center gap-2 self-end md:self-center">
                      <button
                        onClick={() => handleUpdateLeaveStatus(leave.id, 'APPROVED')}
                        className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1 shadow-sm"
                      >
                        <Check className="w-3.5 h-3.5" />
                        Approve
                      </button>
                      <button
                        onClick={() => handleUpdateLeaveStatus(leave.id, 'REJECTED')}
                        className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1 shadow-sm"
                      >
                        <X className="w-3.5 h-3.5" />
                        Reject
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'grievances' && (
        <div className="space-y-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-6 shadow-sm">
            <h2 className="font-bold text-gray-900 dark:text-white mb-2">Confidential Grievance & Employee Relations Hub</h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-6">
              AI automatically classifies urgency, protects privacy, detects burnout flight risks, and drafts resolution protocols.
            </p>

            <div className="space-y-4">
              {grievances.map(g => (
                <div key={g.id} className="p-5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/30 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-gray-900 dark:text-white">{g.subject}</span>
                      <span className="text-xs px-2 py-0.5 rounded bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300">
                        {g.category}
                      </span>
                    </div>
                    <span className="text-xs font-semibold text-amber-500 uppercase">{g.status}</span>
                  </div>

                  <p className="text-xs text-gray-600 dark:text-gray-300">
                    {g.details}
                  </p>

                  {g.ai_analysis && (
                    <div className="p-3 bg-purple-50/60 dark:bg-purple-950/40 border border-purple-100 dark:border-purple-900/50 rounded-lg text-xs space-y-1">
                      <div className="flex items-center gap-2 font-bold text-purple-700 dark:text-purple-300">
                        <Sparkles className="w-3 h-3" />
                        AI Triage Urgency: {g.ai_analysis.urgency} | Sentiment: {g.ai_analysis.sentiment_score}
                      </div>
                      <p className="text-gray-700 dark:text-gray-300">
                        <strong>Action Plan:</strong> {g.ai_analysis.recommended_action}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'attendance' && attendance && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700">
            <span className="text-xs font-medium text-gray-400">Total Workforce</span>
            <p className="text-3xl font-extrabold text-gray-900 dark:text-white mt-2">{attendance.total_workforce}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700">
            <span className="text-xs font-medium text-emerald-500">Present Today</span>
            <p className="text-3xl font-extrabold text-emerald-600 mt-2">{attendance.present_count}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700">
            <span className="text-xs font-medium text-indigo-500">Working Remotely</span>
            <p className="text-3xl font-extrabold text-indigo-600 mt-2">{attendance.remote_count}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700">
            <span className="text-xs font-medium text-purple-500">Punctuality Score</span>
            <p className="text-3xl font-extrabold text-purple-600 mt-2">{attendance.avg_punctuality_score}%</p>
          </div>
        </div>
      )}

      {activeTab === 'payroll' && payroll && (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">Current Payroll Cycle ({payroll.cycle_month})</h3>
              <p className="text-xs text-gray-500">Synced directly with ERP cost centers</p>
            </div>
            <span className="px-3 py-1 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 rounded-full font-bold text-xs">
              {payroll.status}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-xl">
              <span className="text-xs text-gray-400">Total Disbursed Net</span>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">₹{payroll.total_disbursed.toLocaleString('en-IN')}</p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-xl">
              <span className="text-xs text-gray-400">Tax Withholding (TDS)</span>
              <p className="text-2xl font-bold text-indigo-600 mt-1">₹{payroll.tax_withheld.toLocaleString('en-IN')}</p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-xl">
              <span className="text-xs text-gray-400">EPF & Employee Benefits</span>
              <p className="text-2xl font-bold text-purple-600 mt-1">₹{payroll.benefits_paid.toLocaleString('en-IN')}</p>
            </div>
          </div>
        </div>
      )}

      {/* Leave Application Modal */}
      {showApplyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 w-full max-w-md space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">Submit Leave Petition</h3>
              <button onClick={() => setShowApplyModal(false)} className="text-gray-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleApplyLeave} className="space-y-4">
              <div>
                <label className="text-xs font-medium text-gray-700 dark:text-gray-300">Leave Category</label>
                <select
                  value={leaveType}
                  onChange={(e) => setLeaveType(e.target.value)}
                  className="w-full mt-1 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 p-2.5 text-sm text-gray-900 dark:text-white"
                >
                  <option>Casual Leave</option>
                  <option>Sick Leave</option>
                  <option>Earned Leave</option>
                  <option>Compassionate / Emergency</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-700 dark:text-gray-300">Start Date</label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full mt-1 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 p-2.5 text-sm text-gray-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-700 dark:text-gray-300">End Date</label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full mt-1 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 p-2.5 text-sm text-gray-900 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-gray-700 dark:text-gray-300">Reason</label>
                <textarea
                  rows={3}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Provide context for AI workload rebalancing..."
                  className="w-full mt-1 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 p-2.5 text-sm text-gray-900 dark:text-white"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowApplyModal(false)}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-xl text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={applying}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-semibold shadow-md"
                >
                  {applying ? 'Submitting...' : 'Submit to AI Officer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

