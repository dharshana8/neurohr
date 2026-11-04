import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  ArrowLeft,
  Briefcase,
  TrendingUp,
  AlertTriangle,
  Brain,
  Sparkles,
  CheckCircle2,
  XCircle,
  Compass,
  HeartPulse,
  DollarSign,
  Target,
  RefreshCw,
  Lightbulb,
  Layers,
  Shield
} from 'lucide-react';

interface Employee360Data {
  basic_info: {
    employee_id: string;
    name: string;
    department: string;
    role: string;
    manager: string;
    joining_date: string;
    employment_status: string;
  };
  professional_info: {
    experience: number;
    skills: string[];
    performance_score: number;
    engagement_score: number;
    overtime: number;
    promotion_history: number;
    manager_feedback: string;
  };
  compensation: {
    accessible: boolean;
    salary: number | null;
    currency: string | null;
    message: string | null;
  };
  attrition: {
    is_available: boolean;
    estimated_attrition_risk: number | null;
    risk_band: string | null;
    prediction_timestamp: string | null;
    model_version: string | null;
    explanation_factors: any[];
    message: string | null;
  };
  skill_gap?: any;
  career_path: {
    is_available: boolean;
    current_role: string | null;
    target_role: string | null;
    status: string | null;
    recommended_milestones: any[];
    development_actions: string[];
    disclaimer: string;
    message: string | null;
  };
  sentiment: {
    accessible: boolean;
    is_available: boolean;
    recent_sentiment: string | null;
    sentiment_scores: Record<string, number> | null;
    feedback_count: number;
    themes: string[];
    trend: string | null;
    message: string | null;
  };
  ai_insights: {
    is_available: boolean;
    summary: string;
    strengths: string[];
    key_areas_requiring_attention: string[];
    recommended_hr_actions: string[];
    generated_at: string;
  };
}

type TabType = 'overview' | 'performance' | 'attrition' | 'sentiment' | 'ai_insights';

export default function EmployeeProfile() {
  const { employeeId } = useParams<{ employeeId: string }>();
  const navigate = useNavigate();

  const [data, setData] = useState<Employee360Data | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchProfile = async () => {
    if (!employeeId) return;
    setIsLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await axios.get<Employee360Data>(
        `http://localhost:8000/api/v1/workforce/employees/${employeeId}/360`,
        { headers }
      );
      setData(res.data);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          'Failed to load Employee 360° Profile. Ensure the employee ID is valid and you have authorized tenant access.'
      );
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, [employeeId]);

  if (isLoading) {
    return (
      <div className="p-8 max-w-7xl mx-auto space-y-6">
        <div className="flex items-center gap-3">
          <div className="skeleton h-10 w-10 rounded-full" />
          <div className="space-y-2">
            <div className="skeleton h-6 w-48 rounded" />
            <div className="skeleton h-4 w-32 rounded" />
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="skeleton h-28 rounded-2xl" />
          ))}
        </div>
        <div className="skeleton h-96 rounded-2xl" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 max-w-4xl mx-auto text-center space-y-4">
        <div className="w-16 h-16 rounded-full bg-red-50 dark:bg-red-950/40 text-red-500 mx-auto flex items-center justify-center">
          <AlertTriangle className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">Profile Unavailable</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400">{error}</p>
        <button
          onClick={() => navigate('/dashboard/workforce/employees')}
          className="mt-4 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs transition"
        >
          Return to Employee Directory
        </button>
      </div>
    );
  }

  const { basic_info, professional_info, compensation, attrition, sentiment, ai_insights } = data;

  const tabs: { id: TabType; label: string; icon: any; count?: number | string }[] = [
    { id: 'overview', label: 'Overview', icon: UserCircleIcon },
    { id: 'performance', label: 'Performance', icon: TrendingUp },
    { id: 'attrition', label: 'Attrition Risk', icon: AlertTriangle, count: (attrition.is_available && attrition.risk_band) ? attrition.risk_band : undefined },
    { id: 'sentiment', label: 'Sentiment', icon: HeartPulse, count: (sentiment.is_available && sentiment.recent_sentiment) ? sentiment.recent_sentiment : undefined },
    { id: 'ai_insights', label: 'AI Insights', icon: Brain }
  ];

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6 page-enter">
      {/* Top Navigation & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <button
          onClick={() => navigate('/dashboard/workforce/employees')}
          className="inline-flex items-center gap-2 text-xs font-semibold text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Directory
        </button>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setIsRefreshing(true);
              fetchProfile();
            }}
            disabled={isRefreshing}
            className="px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-xs font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-1.5 shadow-xs transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh 360° Data
          </button>
        </div>
      </div>

      {/* Header Profile Hero Card */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-6 shadow-xs relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-indigo-500 to-purple-600 text-white flex items-center justify-center text-xl font-bold shadow-md flex-shrink-0">
              {basic_info.name.slice(0, 2).toUpperCase()}
            </div>
            <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-2.5">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{basic_info.name}</h1>
                <span className="font-mono text-xs px-2.5 py-0.5 rounded-md bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 font-semibold">
                  {basic_info.employee_id}
                </span>
                <span
                  className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                    basic_info.employment_status.toLowerCase() === 'active'
                      ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                  }`}
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  {basic_info.employment_status}
                </span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-300 font-medium">
                {basic_info.role} &bull; <span className="text-indigo-600 dark:text-indigo-400 font-semibold">{basic_info.department}</span>
              </p>
              <p className="text-xs text-gray-400 flex items-center gap-2 pt-1">
                <span>Manager: <strong className="text-gray-700 dark:text-gray-300 font-medium">{basic_info.manager}</strong></span>
                <span>&bull;</span>
                <span>Joined: {new Date(basic_info.joining_date).toLocaleDateString()}</span>
              </p>
            </div>
          </div>

          {/* Quick Stat Pill Cards */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="px-4 py-3 rounded-xl bg-gray-50 dark:bg-gray-700/40 border border-gray-100 dark:border-gray-700/60 min-w-[110px]">
              <span className="text-[11px] text-gray-400 block font-medium">Performance</span>
              <span className="text-lg font-bold text-gray-900 dark:text-white tabular-nums">
                {professional_info.performance_score.toFixed(1)} / 5.0
              </span>
            </div>
            <div className="px-4 py-3 rounded-xl bg-gray-50 dark:bg-gray-700/40 border border-gray-100 dark:border-gray-700/60 min-w-[110px]">
              <span className="text-[11px] text-gray-400 block font-medium">Engagement</span>
              <span className="text-lg font-bold text-gray-900 dark:text-white tabular-nums">
                {professional_info.engagement_score.toFixed(1)} / 5.0
              </span>
            </div>
            {compensation.accessible && compensation.salary !== null && (
              <div className="px-4 py-3 rounded-xl bg-indigo-50 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-800/40 min-w-[120px]">
                <span className="text-[11px] text-indigo-500 dark:text-indigo-400 block font-medium">Compensation</span>
                <span className="text-lg font-bold text-indigo-900 dark:text-indigo-200 tabular-nums">
                  ₹{compensation.salary.toLocaleString('en-IN')}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-1 border-t border-gray-100 dark:border-gray-700 mt-6 pt-3 overflow-x-auto scrollbar-none">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition flex-shrink-0 ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-xs'
                    : 'text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-700/50'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
                {tab.count && (
                  <span
                    className={`px-1.5 py-0.2 rounded-md text-[10px] ${
                      isActive ? 'bg-indigo-700 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                    }`}
                  >
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab 1: Overview */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {/* AI Executive Summary Card */}
            <div className="bg-gradient-to-br from-indigo-50/70 via-white to-purple-50/70 dark:from-gray-800 dark:via-gray-800 dark:to-indigo-950/20 rounded-2xl border border-indigo-100 dark:border-indigo-900/40 p-6 shadow-xs">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                <h3 className="text-sm font-bold text-gray-900 dark:text-white">AI Executive 360° Summary</h3>
              </div>
              <p className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed">{ai_insights.summary}</p>
            </div>

            {/* Basic & Professional Information */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-6 shadow-xs space-y-4">
              <h3 className="text-sm font-bold text-gray-900 dark:text-white">Professional Background</h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
                <div>
                  <span className="text-gray-400 block mb-0.5">Years Experience</span>
                  <span className="font-semibold text-gray-800 dark:text-gray-200">{professional_info.experience} years</span>
                </div>
                <div>
                  <span className="text-gray-400 block mb-0.5">Overtime Worked</span>
                  <span className="font-semibold text-gray-800 dark:text-gray-200">{professional_info.overtime} hrs / mo</span>
                </div>
                <div>
                  <span className="text-gray-400 block mb-0.5">Promotion History</span>
                  <span className="font-semibold text-gray-800 dark:text-gray-200">{professional_info.promotion_history} recorded</span>
                </div>
                <div>
                  <span className="text-gray-400 block mb-0.5">Department</span>
                  <span className="font-semibold text-gray-800 dark:text-gray-200">{basic_info.department}</span>
                </div>
                <div>
                  <span className="text-gray-400 block mb-0.5">Role</span>
                  <span className="font-semibold text-gray-800 dark:text-gray-200">{basic_info.role}</span>
                </div>
                <div>
                  <span className="text-gray-400 block mb-0.5">Manager Feedback</span>
                  <span className="font-semibold text-gray-800 dark:text-gray-200 truncate block" title={professional_info.manager_feedback}>
                    {professional_info.manager_feedback ? 'Feedback on file' : 'None recorded'}
                  </span>
                </div>
              </div>
            </div>

            {/* Skills Badges */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-6 shadow-xs space-y-3">
              <h3 className="text-sm font-bold text-gray-900 dark:text-white">Active Competencies</h3>
              <div className="flex flex-wrap gap-2">
                {professional_info.skills.map((skill, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column: Status Cards */}
          <div className="space-y-6">
            {/* Compensation Card */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-6 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-emerald-500" />
                  Compensation
                </h3>
                {compensation.accessible ? (
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/30 text-emerald-600 dark:text-emerald-400">
                    Verified
                  </span>
                ) : (
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-500">
                    Restricted
                  </span>
                )}
              </div>
              {compensation.accessible && compensation.salary !== null ? (
                <div className="p-4 bg-emerald-50/50 dark:bg-emerald-950/20 rounded-xl border border-emerald-100 dark:border-emerald-900/30">
                  <span className="text-xs text-gray-500 dark:text-gray-400 block mb-1">Annual Base Salary</span>
                  <span className="text-2xl font-bold text-gray-900 dark:text-white font-mono">
                    ₹{compensation.salary.toLocaleString('en-IN')}{' '}
                    <span className="text-xs font-normal text-gray-400">{compensation.currency || 'INR'}</span>
                  </span>
                </div>
              ) : (
                <div className="p-4 bg-gray-50 dark:bg-gray-700/40 rounded-xl text-xs text-gray-500">
                  {compensation.message || 'Access restricted by role permissions.'}
                </div>
              )}
            </div>

            {/* Attrition Risk Pill */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-6 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                  Attrition Assessment
                </h3>
              </div>
              {attrition.is_available && attrition.estimated_attrition_risk !== null ? (
                <div className="space-y-3">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-gray-500">Estimated Attrition Risk:</span>
                    <span className="font-mono font-bold text-gray-900 dark:text-white">
                      {(attrition.estimated_attrition_risk * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-gray-500">Risk Band:</span>
                    <span
                      className={`px-2.5 py-0.5 rounded-full font-bold text-[11px] ${
                        attrition.risk_band === 'HIGH'
                          ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
                          : attrition.risk_band === 'MEDIUM'
                          ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
                          : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'
                      }`}
                    >
                      {attrition.risk_band} RISK
                    </span>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-gray-400">
                  {attrition.message || 'Attrition risk has not been estimated for this employee.'}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Performance */}
      {activeTab === 'performance' && (
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-6 shadow-xs space-y-6">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-gray-900 dark:text-white">Performance & Engagement Diagnostics</h2>
              <p className="text-xs text-gray-500">Objective evaluations from appraisals, evaluations, and manager records.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-5 rounded-2xl bg-gray-50 dark:bg-gray-700/30 border border-gray-100 dark:border-gray-700 space-y-2">
              <span className="text-xs text-gray-400 font-medium">Performance Rating</span>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-indigo-600 dark:text-indigo-400">
                  {professional_info.performance_score.toFixed(1)}
                </span>
                <span className="text-xs text-gray-400">/ 5.0</span>
              </div>
              <p className="text-[11px] text-gray-500">Based on recent organizational performance review cycle.</p>
            </div>

            <div className="p-5 rounded-2xl bg-gray-50 dark:bg-gray-700/30 border border-gray-100 dark:border-gray-700 space-y-2">
              <span className="text-xs text-gray-400 font-medium">Engagement Score</span>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400">
                  {professional_info.engagement_score.toFixed(1)}
                </span>
                <span className="text-xs text-gray-400">/ 5.0</span>
              </div>
              <p className="text-[11px] text-gray-500">Workplace survey and team engagement participation index.</p>
            </div>

            <div className="p-5 rounded-2xl bg-gray-50 dark:bg-gray-700/30 border border-gray-100 dark:border-gray-700 space-y-2">
              <span className="text-xs text-gray-400 font-medium">Promotion Milestones</span>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-purple-600 dark:text-purple-400">
                  {professional_info.promotion_history}
                </span>
                <span className="text-xs text-gray-400">promotions</span>
              </div>
              <p className="text-[11px] text-gray-500">Total upward career milestone advancements recorded.</p>
            </div>
          </div>

          {professional_info.manager_feedback && (
            <div className="p-5 rounded-2xl bg-gray-50/70 dark:bg-gray-700/20 border border-gray-100 dark:border-gray-700 space-y-2">
              <h3 className="text-xs font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Manager Evaluation Notes</h3>
              <p className="text-xs text-gray-600 dark:text-gray-300 leading-relaxed italic">
                "{professional_info.manager_feedback}"
              </p>
            </div>
          )}
        </div>
      )}



      {/* Tab 4: Attrition */}
      {activeTab === 'attrition' && (
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-6 shadow-xs space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-gray-900 dark:text-white">Estimated Attrition Risk Model</h2>
              <p className="text-xs text-gray-500">
                Algorithmic flight-risk probability and contributing SHAP explanation factors.
              </p>
            </div>
            {attrition.is_available && (
              <span
                className={`px-3 py-1 rounded-full font-bold text-xs ${
                  attrition.risk_band === 'HIGH'
                    ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
                    : attrition.risk_band === 'MEDIUM'
                    ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
                    : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'
                }`}
              >
                {attrition.risk_band} RISK
              </span>
            )}
          </div>

          {attrition.is_available && attrition.estimated_attrition_risk !== null ? (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/30">
                  <span className="text-xs text-gray-400 block mb-1">Estimated Attrition Risk</span>
                  <span className="text-3xl font-bold font-mono text-gray-900 dark:text-white">
                    {(attrition.estimated_attrition_risk * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/30">
                  <span className="text-xs text-gray-400 block mb-1">Model Version</span>
                  <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">
                    {attrition.model_version || 'Production v1'}
                  </span>
                </div>
                <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/30">
                  <span className="text-xs text-gray-400 block mb-1">Evaluated On</span>
                  <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">
                    {attrition.prediction_timestamp ? new Date(attrition.prediction_timestamp).toLocaleString() : 'N/A'}
                  </span>
                </div>
              </div>

              {/* SHAP Feature Breakdown Cards */}
              {attrition.explanation_factors && attrition.explanation_factors.length > 0 && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xs font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                        Feature Contributions (SHAP Analysis)
                      </h3>
                      <p className="text-[11px] text-gray-400 mt-0.5">
                        Factors that contributed to the model prediction (non-causal algorithmic indicators).
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Factors increasing risk */}
                    <div className="p-4 rounded-xl bg-red-50/40 dark:bg-red-950/20 border border-red-100 dark:border-red-900/40 space-y-3">
                      <div className="flex items-center gap-2 text-red-700 dark:text-red-400 text-xs font-bold uppercase tracking-wider">
                        <AlertTriangle className="w-4 h-4" />
                        Top Risk Factors (Contributed to Predicted Risk)
                      </div>
                      <div className="space-y-2">
                        {attrition.explanation_factors
                          .filter((f: any) => f.direction === 'INCREASES_RISK' || f.impact === 'INCREASES_RISK' || (typeof f.contribution === 'number' && f.contribution > 0) || (typeof f.shap_value === 'number' && f.shap_value > 0))
                          .map((f: any, idx: number) => {
                            const val = f.contribution !== undefined ? f.contribution : (f.shap_value !== undefined ? f.shap_value : null);
                            const name = f.display_name || (f.feature ? f.feature.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase()) : (f.name || 'Factor'));
                            return (
                              <div
                                key={idx}
                                className="p-2.5 rounded-lg bg-white dark:bg-gray-800 border border-red-100 dark:border-red-900/30 flex items-center justify-between text-xs"
                              >
                                <div>
                                  <span className="font-semibold text-gray-800 dark:text-gray-200">↑ {name}</span>
                                  <p className="text-[11px] text-gray-500 mt-0.5">{f.description || 'Contributed to higher estimated attrition risk in the model.'}</p>
                                </div>
                                {val !== null && typeof val === 'number' && (
                                  <span className="font-mono text-red-600 dark:text-red-400 font-bold ml-2">
                                    +{Math.abs(val).toFixed(3)}
                                  </span>
                                )}
                              </div>
                            );
                          })}
                        {attrition.explanation_factors.filter((f: any) => f.direction === 'INCREASES_RISK' || f.impact === 'INCREASES_RISK' || (typeof f.contribution === 'number' && f.contribution > 0) || (typeof f.shap_value === 'number' && f.shap_value > 0)).length === 0 && (
                          <p className="text-xs text-gray-400 italic p-2">No factors significantly increased the model risk score.</p>
                        )}
                      </div>
                    </div>

                    {/* Protective factors */}
                    <div className="p-4 rounded-xl bg-emerald-50/40 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/40 space-y-3">
                      <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-400 text-xs font-bold uppercase tracking-wider">
                        <Shield className="w-4 h-4" />
                        Protective Factors (Contributed to Reducing Risk)
                      </div>
                      <div className="space-y-2">
                        {attrition.explanation_factors
                          .filter((f: any) => f.direction === 'REDUCES_RISK' || f.impact === 'protective' || (typeof f.contribution === 'number' && f.contribution < 0) || (typeof f.shap_value === 'number' && f.shap_value < 0))
                          .map((f: any, idx: number) => {
                            const val = f.contribution !== undefined ? f.contribution : (f.shap_value !== undefined ? f.shap_value : null);
                            const name = f.display_name || (f.feature ? f.feature.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase()) : (f.name || 'Factor'));
                            return (
                              <div
                                key={idx}
                                className="p-2.5 rounded-lg bg-white dark:bg-gray-800 border border-emerald-100 dark:border-emerald-900/30 flex items-center justify-between text-xs"
                              >
                                <div>
                                  <span className="font-semibold text-gray-800 dark:text-gray-200">↓ {name}</span>
                                  <p className="text-[11px] text-gray-500 mt-0.5">{f.description || 'Contributed to reducing the model attrition risk prediction.'}</p>
                                </div>
                                {val !== null && typeof val === 'number' && (
                                  <span className="font-mono text-emerald-600 dark:text-emerald-400 font-bold ml-2">
                                    -{Math.abs(val).toFixed(3)}
                                  </span>
                                )}
                              </div>
                            );
                          })}
                        {attrition.explanation_factors.filter((f: any) => f.direction === 'REDUCES_RISK' || f.impact === 'protective' || (typeof f.contribution === 'number' && f.contribution < 0) || (typeof f.shap_value === 'number' && f.shap_value < 0)).length === 0 && (
                          <p className="text-xs text-gray-400 italic p-2">No factors significantly reduced the model risk score.</p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-8 text-center text-xs text-gray-400">
              {attrition.message || 'Estimated attrition risk evaluation has not yet been computed for this employee.'}
            </div>
          )}
        </div>
      )}



      {/* Tab 6: Sentiment */}
      {activeTab === 'sentiment' && (
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-6 shadow-xs space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-gray-900 dark:text-white">Workplace Sentiment Telemetry</h2>
              <p className="text-xs text-gray-500">Derived from verified employee survey feedback and sentiment models.</p>
            </div>
          </div>

          {!sentiment.accessible ? (
            <div className="p-8 text-center text-xs text-gray-400">
              {sentiment.message || 'Access to employee sentiment telemetry is restricted for your role.'}
            </div>
          ) : sentiment.is_available ? (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/30">
                  <span className="text-xs text-gray-400 block mb-1">Recent Sentiment</span>
                  <span
                    className={`text-lg font-bold ${
                      sentiment.recent_sentiment === 'POSITIVE'
                        ? 'text-emerald-600'
                        : sentiment.recent_sentiment === 'NEGATIVE'
                        ? 'text-red-600'
                        : 'text-gray-600'
                    }`}
                  >
                    {sentiment.recent_sentiment}
                  </span>
                </div>
                <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/30">
                  <span className="text-xs text-gray-400 block mb-1">Feedback Submissions</span>
                  <span className="text-lg font-bold text-gray-900 dark:text-white font-mono">
                    {sentiment.feedback_count}
                  </span>
                </div>
                <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/30">
                  <span className="text-xs text-gray-400 block mb-1">Observed Trend</span>
                  <span className="text-lg font-bold text-indigo-600 dark:text-indigo-400">
                    {sentiment.trend || 'STABLE'}
                  </span>
                </div>
              </div>

              {sentiment.themes.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-xs font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Top Themes</h3>
                  <div className="flex flex-wrap gap-2">
                    {sentiment.themes.map((theme, idx) => (
                      <span key={idx} className="px-3 py-1 rounded-lg text-xs font-semibold bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                        {theme}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-8 text-center text-xs text-gray-400">
              {sentiment.message || 'No direct survey feedback submitted yet.'}
            </div>
          )}
        </div>
      )}

      {/* Tab 7: AI Insights */}
      {activeTab === 'ai_insights' && (
        <div className="space-y-6">
          <div className="bg-gradient-to-br from-indigo-50/80 via-white to-purple-50/80 dark:from-gray-800 dark:via-gray-800 dark:to-indigo-950/20 rounded-2xl border border-indigo-100 dark:border-indigo-900/40 p-6 shadow-xs space-y-4">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              <h2 className="text-base font-bold text-gray-900 dark:text-white">AI Executive Summary</h2>
            </div>
            <p className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed font-normal">
              {ai_insights.summary}
            </p>
            <p className="text-[10px] text-gray-400">
              Synthesized on: {new Date(ai_insights.generated_at).toLocaleString()} using verified backend telemetry.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Strengths */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-6 shadow-xs space-y-3">
              <h3 className="text-xs font-bold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                Key Strengths
              </h3>
              <ul className="space-y-2 text-xs text-gray-600 dark:text-gray-300">
                {ai_insights.strengths.map((s, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-emerald-500 font-bold">&bull;</span>
                    <span>{s}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Areas Requiring Attention */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-6 shadow-xs space-y-3">
              <h3 className="text-xs font-bold text-amber-700 dark:text-amber-400 uppercase tracking-wider flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                Attention Areas
              </h3>
              <ul className="space-y-2 text-xs text-gray-600 dark:text-gray-300">
                {ai_insights.key_areas_requiring_attention.map((a, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-amber-500 font-bold">&bull;</span>
                    <span>{a}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Recommended Actions */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-6 shadow-xs space-y-3">
              <h3 className="text-xs font-bold text-indigo-700 dark:text-indigo-400 uppercase tracking-wider flex items-center gap-2">
                <Lightbulb className="w-4 h-4" />
                Recommended HR Actions
              </h3>
              <ul className="space-y-2 text-xs text-gray-600 dark:text-gray-300">
                {ai_insights.recommended_hr_actions.map((act, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-indigo-500 font-bold">&bull;</span>
                    <span>{act}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function UserCircleIcon(props: any) {
  return <Briefcase {...props} />;
}
