import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { api } from '../../lib/api';
import {
  Compass, CheckCircle2, Circle, Sparkles,
  ArrowRight, ShieldCheck, X, BookOpen, GraduationCap
} from 'lucide-react';

interface Milestone {
  title: string;
  description: string;
  completed: boolean;
  target_date?: string;
}

interface CareerPath {
  career_path_id: string;
  employee_id: string;
  employee_name: string;
  current_role: string;
  target_role: string;
  estimated_skill_coverage: number;
  required_skills: string[];
  current_skills: string[];
  missing_skills: string[];
  recommended_actions: string[];
  milestones: Milestone[];
  status: string;
  performance_context?: {
    performance_score: number;
    experience_years: number;
    notes: string;
  };
  is_ai_assisted: boolean;
  disclaimer: string;
  created_at: string;
  updated_at: string;
}

interface Analytics {
  active_career_paths: number;
  target_roles: { role: string; count: number }[];
  common_development_areas: { area: string; count: number }[];
  status_distribution: Record<string, number>;
}

interface Employee {
  employee_id: string;
  name: string;
  role: string;
}

export default function CareerPathDashboard() {
  const [searchParams] = useSearchParams();
  const [paths, setPaths] = useState<CareerPath[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [loading, setLoading] = useState(true);

  // Modal State
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [selectedEmpId, setSelectedEmpId] = useState(searchParams.get('employee_id') || '');
  const [selectedTargetRole, setSelectedTargetRole] = useState('Senior Backend Developer');
  const [generating, setGenerating] = useState(false);
  const [aiPlanModal, setAiPlanModal] = useState<any | null>(null);
  const [generatingPlanId, setGeneratingPlanId] = useState<string | null>(null);

  const handleGenerateAiPlan = async (employeeId: string, targetRole: string) => {
    setGeneratingPlanId(employeeId);
    try {
      const res = await api.post('/ai/explain/career', {
        employee_id: employeeId,
        target_role: targetRole
      });
      setAiPlanModal(res.data);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to generate AI development plan');
    } finally {
      setGeneratingPlanId(null);
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const [pathsRes, analyticsRes, empRes] = await Promise.allSettled([
        api.get('/intelligence/career-paths'),
        api.get('/intelligence/career-paths/analytics'),
        api.get('/workforce/employees')
      ]);

      if (pathsRes.status === 'fulfilled') setPaths(pathsRes.value.data);
      if (analyticsRes.status === 'fulfilled') setAnalytics(analyticsRes.value.data);
      if (empRes.status === 'fulfilled') setEmployees(empRes.value.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleToggleMilestone = async (path: CareerPath, mIndex: number) => {
    const updatedMilestones = [...path.milestones];
    updatedMilestones[mIndex].completed = !updatedMilestones[mIndex].completed;

    try {
      await api.put(`/intelligence/career-paths/${path.career_path_id}`, {
        milestones: updatedMilestones
      });
      setPaths(prev => prev.map(p => (p.career_path_id === path.career_path_id ? { ...p, milestones: updatedMilestones } : p)));
    } catch (err) {
      alert('Failed to update milestone status');
    }
  };

  const handleStatusChange = async (pathId: string, newStatus: string) => {
    try {
      await api.put(`/intelligence/career-paths/${pathId}`, {
        status: newStatus
      });
      setPaths(prev => prev.map(p => (p.career_path_id === pathId ? { ...p, status: newStatus } : p)));
    } catch (err) {
      alert('Failed to update status');
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEmpId || !selectedTargetRole) return;
    setGenerating(true);
    try {
      await api.post('/intelligence/career-paths/generate', {
        employee_id: selectedEmpId,
        target_role: selectedTargetRole
      });
      setShowGenerateModal(false);
      loadData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Generation failed');
    } finally {
      setGenerating(false);
    }
  };

  const filteredPaths = paths.filter(p => {
    if (statusFilter === 'ALL') return true;
    return p.status === statusFilter;
  });

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-8 page-enter">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Personalized Career Pathing</h2>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300">
              AI-Assisted
            </span>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Structured skill acquisition roadmaps and milestone progression tracking toward target career positions.
          </p>
        </div>

        <button
          onClick={() => setShowGenerateModal(true)}
          className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-xl text-sm font-semibold shadow-md shadow-indigo-500/25 transition-all"
        >
          <Sparkles className="w-4 h-4" />
          Generate AI Career Path
        </button>
      </div>

      {/* Ethical Disclaimer Banner */}
      <div className="p-4 rounded-2xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200/70 dark:border-amber-900/40 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-amber-900 dark:text-amber-200 leading-relaxed">
          <strong className="font-semibold">AI Decision-Support Guidance: </strong>
          Career path recommendations are generated to support employee professional development and capability building. All milestones and plans represent advisory career roadmaps and <strong>do not guarantee promotion</strong> or automated organizational changes.
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-100 dark:border-gray-700 shadow-sm">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Active Career Paths</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
            {loading ? '—' : analytics?.active_career_paths ?? 0}
          </p>
          <p className="text-xs text-gray-400 mt-1">In progress across organization</p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-100 dark:border-gray-700 shadow-sm">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Total Generated</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
            {loading ? '—' : paths.length}
          </p>
          <p className="text-xs text-gray-400 mt-1">Career development plans</p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-100 dark:border-gray-700 shadow-sm">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Completed Plans</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
            {loading ? '—' : analytics?.status_distribution?.COMPLETED ?? 0}
          </p>
          <p className="text-xs text-emerald-600 dark:text-emerald-400 mt-1 font-medium">Milestones fulfilled</p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-100 dark:border-gray-700 shadow-sm">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Target Roles Identified</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
            {loading ? '—' : analytics?.target_roles?.length ?? 0}
          </p>
          <p className="text-xs text-gray-400 mt-1">Distinct advancement targets</p>
        </div>
      </div>

      {/* Status Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-gray-200 dark:border-gray-800 pb-1">
        {['ALL', 'ACTIVE', 'DRAFT', 'COMPLETED', 'ARCHIVED'].map(s => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`px-4 py-2 text-xs font-bold rounded-lg uppercase tracking-wider transition-all ${
              statusFilter === s
                ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400'
                : 'text-gray-500 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            {s} ({s === 'ALL' ? paths.length : paths.filter(p => p.status === s).length})
          </button>
        ))}
      </div>

      {/* Career Path Cards */}
      {filteredPaths.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-3xl border border-gray-100 dark:border-gray-700 p-12 text-center">
          <Compass className="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600 mb-3" />
          <h3 className="text-base font-bold text-gray-900 dark:text-white">No career paths found</h3>
          <p className="text-xs text-gray-400 max-w-sm mx-auto mt-1 mb-6">
            Click Generate AI Career Path to formulate a progressive roadmap for any employee.
          </p>
          <button
            onClick={() => setShowGenerateModal(true)}
            className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold"
          >
            Generate Career Path
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {filteredPaths.map(path => {
            const completedCount = path.milestones.filter(m => m.completed).length;
            const totalMilestones = path.milestones.length;
            const progressPct = totalMilestones > 0 ? Math.round((completedCount / totalMilestones) * 100) : 0;

            return (
              <div
                key={path.career_path_id}
                className="bg-white dark:bg-gray-800 rounded-3xl border border-gray-100 dark:border-gray-700 shadow-sm p-6 lg:p-8 space-y-6"
              >
                {/* Header Row */}
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-3">
                      <h3 className="text-xl font-bold text-gray-900 dark:text-white">{path.employee_name}</h3>
                      <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300">
                        {path.employee_id}
                      </span>
                      {path.is_ai_assisted && (
                        <span className="text-[11px] px-2 py-0.5 rounded-full font-medium bg-purple-50 dark:bg-purple-950/50 text-purple-700 dark:text-purple-300 flex items-center gap-1">
                          <Sparkles className="w-3 h-3" /> AI-Assisted Recommendation
                        </span>
                      )}
                    </div>
                    {/* Role progression */}
                    <div className="flex items-center gap-2 mt-2 text-sm text-gray-600 dark:text-gray-300">
                      <span className="font-semibold text-gray-800 dark:text-gray-200">{path.current_role}</span>
                      <ArrowRight className="w-4 h-4 text-indigo-500" />
                      <span className="font-bold text-indigo-600 dark:text-indigo-400">{path.target_role}</span>
                    </div>
                  </div>

                  {/* Status & Skill Coverage Badge */}
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block">Estimated Coverage</span>
                      <span className="text-sm font-bold text-gray-900 dark:text-white">{path.estimated_skill_coverage}%</span>
                    </div>

                    <button
                      onClick={() => handleGenerateAiPlan(path.employee_id, path.target_role)}
                      disabled={generatingPlanId === path.employee_id}
                      className="px-3 py-1.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs flex items-center gap-1.5 transition-all disabled:opacity-50"
                      title="Generate customized Grok AI upskilling plan"
                    >
                      <Sparkles className={`w-3.5 h-3.5 ${generatingPlanId === path.employee_id ? 'animate-spin' : ''}`} />
                      {generatingPlanId === path.employee_id ? 'Synthesizing...' : 'AI Upskilling Plan'}
                    </button>

                    <select
                      value={path.status}
                      onChange={e => handleStatusChange(path.career_path_id, e.target.value)}
                      className="text-xs font-bold px-3 py-1.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-200 focus:outline-none"
                    >
                      <option value="ACTIVE">ACTIVE</option>
                      <option value="DRAFT">DRAFT</option>
                      <option value="COMPLETED">COMPLETED</option>
                      <option value="ARCHIVED">ARCHIVED</option>
                    </select>
                  </div>
                </div>

                {/* Milestone Progress Bar */}
                <div>
                  <div className="flex items-center justify-between text-xs font-semibold mb-2">
                    <span className="text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Milestone Progression ({completedCount} of {totalMilestones} fulfilled)
                    </span>
                    <span className="text-indigo-600 dark:text-indigo-400 font-bold">{progressPct}%</span>
                  </div>
                  <div className="w-full bg-gray-100 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                    <div
                      className="h-full bg-indigo-600 rounded-full transition-all duration-500"
                      style={{ width: `${progressPct}%` }}
                    />
                  </div>
                </div>

                {/* Milestones List (Interactive Checkboxes) */}
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Career Milestones</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {path.milestones.map((m, mIdx) => (
                      <div
                        key={mIdx}
                        onClick={() => handleToggleMilestone(path, mIdx)}
                        className={`p-4 rounded-2xl border transition-all cursor-pointer flex items-start gap-3 ${
                          m.completed
                            ? 'bg-emerald-50/50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-900/50'
                            : 'bg-gray-50 dark:bg-gray-900/40 border-gray-100 dark:border-gray-800 hover:border-gray-200'
                        }`}
                      >
                        <div className="mt-0.5 flex-shrink-0">
                          {m.completed ? (
                            <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                          ) : (
                            <Circle className="w-5 h-5 text-gray-400 hover:text-indigo-500" />
                          )}
                        </div>
                        <div>
                          <p className={`text-sm font-semibold ${
                            m.completed ? 'text-emerald-900 dark:text-emerald-200 line-through opacity-80' : 'text-gray-900 dark:text-white'
                          }`}>
                            {m.title}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 leading-relaxed">
                            {m.description}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recommended Actions */}
                {path.recommended_actions.length > 0 && (
                  <div className="p-4 rounded-2xl bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/40">
                    <h4 className="text-xs font-bold text-indigo-900 dark:text-indigo-200 uppercase tracking-wider mb-2">
                      Key Development Actions
                    </h4>
                    <ul className="space-y-1 text-xs text-indigo-800 dark:text-indigo-300">
                      {path.recommended_actions.map((act, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-indigo-500 font-bold">•</span>
                          <span>{act}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Supporting Context & Actions */}
                <div className="flex items-center justify-between pt-2 border-t border-gray-100 dark:border-gray-700/60 text-xs text-gray-400">
                  <span>
                    Performance Score Context: <strong>{path.performance_context?.performance_score ?? '—'} / 5.0</strong> (Advisory)
                  </span>
                  <Link
                    to={`/dashboard/intelligence/skill-gaps/${path.employee_id}?target_role=${encodeURIComponent(path.target_role)}`}
                    className="text-indigo-600 dark:text-indigo-400 font-semibold hover:underline flex items-center gap-1"
                  >
                    View Underlying Skill Gap Analysis <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal: Generate AI Career Path */}
      {showGenerateModal && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl max-w-md w-full p-6 shadow-xl border border-gray-100 dark:border-gray-700 space-y-5 animate-in fade-in">
            <div>
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-purple-600" />
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">Generate Career Path</h3>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Synthesize employee competencies, target role requirements, and milestones into an advisory roadmap.
              </p>
            </div>

            <form onSubmit={handleGenerate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Select Employee
                </label>
                <select
                  value={selectedEmpId}
                  onChange={e => setSelectedEmpId(e.target.value)}
                  required
                  className="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">-- Choose Employee --</option>
                  {employees.map(emp => (
                    <option key={emp.employee_id} value={emp.employee_id}>
                      {emp.name} ({emp.role})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Target Career Role
                </label>
                <input
                  type="text"
                  value={selectedTargetRole}
                  onChange={e => setSelectedTargetRole(e.target.value)}
                  placeholder="e.g. Senior Backend Developer"
                  required
                  className="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowGenerateModal(false)}
                  className="px-4 py-2 rounded-xl text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={generating}
                  className="px-5 py-2 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 shadow-md shadow-indigo-500/25 transition-all disabled:opacity-50"
                >
                  {generating ? 'Generating Roadmap...' : 'Generate Roadmap'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Grok AI Development Plan Modal */}
      {aiPlanModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
          <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-xl w-full border border-gray-100 dark:border-gray-800 shadow-2xl overflow-hidden p-6 space-y-5 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between pb-3 border-b border-gray-100 dark:border-gray-800">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-purple-50 dark:bg-purple-950/50 text-purple-600 dark:text-purple-400 border border-purple-200 dark:border-purple-800">
                  <GraduationCap className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-gray-900 dark:text-white">AI Upskilling & Development Plan</h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Target Role: <span className="font-semibold text-indigo-600 dark:text-indigo-400">{aiPlanModal.target_role}</span></p>
                </div>
              </div>
              <button
                onClick={() => setAiPlanModal(null)}
                className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Timeline pill */}
            <div className="p-3 bg-indigo-50/60 dark:bg-indigo-950/30 rounded-xl border border-indigo-100 dark:border-indigo-900/40 flex items-center justify-between">
              <div>
                <span className="text-[11px] text-gray-400 block font-medium">Estimated Readiness Timeline</span>
                <span className="text-sm font-bold text-indigo-700 dark:text-indigo-300">{aiPlanModal.projected_readiness_timeline || "3-6 months"}</span>
              </div>
              <span className="px-2.5 py-1 text-xs font-bold rounded-lg bg-indigo-600 text-white shadow-xs">Active Progression</span>
            </div>

            {/* Recommended Training */}
            {aiPlanModal.recommended_training_areas?.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Priority Skill Training Areas</p>
                <div className="space-y-1">
                  {aiPlanModal.recommended_training_areas.map((tr: string, i: number) => (
                    <div key={i} className="p-2 rounded-lg bg-gray-50 dark:bg-gray-800/60 border border-gray-100 dark:border-gray-800 text-xs text-gray-700 dark:text-gray-300 flex items-center gap-2">
                      <BookOpen className="w-3.5 h-3.5 text-purple-500 shrink-0" />
                      <span>{tr}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Mentorship suggestions */}
            {aiPlanModal.mentorship_suggestions?.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Mentorship & Shadowing Track</p>
                <div className="space-y-1">
                  {aiPlanModal.mentorship_suggestions.map((m: string, i: number) => (
                    <div key={i} className="p-2 rounded-lg bg-gray-50 dark:bg-gray-800/60 border border-gray-100 dark:border-gray-800 text-xs text-gray-700 dark:text-gray-300 flex items-center gap-2">
                      <Compass className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
                      <span>{m}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Grok Plan Narrative */}
            <div className="p-4 bg-purple-50/50 dark:bg-purple-950/30 rounded-2xl border border-purple-100 dark:border-purple-900/40 space-y-2">
              <div className="flex items-center gap-2 text-purple-700 dark:text-purple-300 text-xs font-bold uppercase tracking-wider">
                <Sparkles className="w-3.5 h-3.5" />
                Grok AI Career Coaching Synthesis
              </div>
              <p className="text-xs text-gray-800 dark:text-gray-200 leading-relaxed font-normal whitespace-pre-wrap">
                {aiPlanModal.plan_summary}
              </p>
            </div>

            {/* Disclaimer */}
            <p className="text-[11px] text-gray-400 dark:text-gray-500 italic">
              {aiPlanModal.disclaimer || "* AI-assisted recommendation. Does not constitute guaranteed promotion or compensation adjustment."}
            </p>

            <button
              onClick={() => setAiPlanModal(null)}
              className="w-full py-2.5 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-xl text-xs font-semibold transition-colors"
            >
              Close Plan
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
