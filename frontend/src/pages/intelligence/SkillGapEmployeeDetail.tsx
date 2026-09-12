import { useState, useEffect } from 'react';
import { useParams, useSearchParams, useNavigate, Link } from 'react-router-dom';
import { api } from '../../lib/api';
import {
  CheckCircle2, AlertTriangle, AlertCircle, ArrowLeft,
  Sparkles, Compass, ShieldCheck
} from 'lucide-react';

interface SkillItem {
  skill: string;
  required_level?: string;
  employee_level?: string;
  status: string;
  explanation: string;
}

interface DevelopmentArea {
  skill: string;
  priority: string;
  recommendation_type: string;
  recommendation: string;
  reason: string;
}

interface AnalysisData {
  analysis_id: string;
  employee_id: string;
  employee_name: string;
  current_role: string;
  target_role: string;
  skill_coverage_score: number;
  matched_count: number;
  missing_count: number;
  partial_count: number;
  total_required_skills: number;
  matched_skills: SkillItem[];
  missing_skills: SkillItem[];
  partial_skills: SkillItem[];
  recommended_development_areas: DevelopmentArea[];
  created_at: string;
}

interface EmployeeData {
  employee_id: string;
  name: string;
  department: string;
  role: string;
  experience: number;
  performance_score: number;
  engagement_score: number;
  skills: string;
}

export default function SkillGapEmployeeDetail() {
  const { employeeId } = useParams<{ employeeId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const [employee, setEmployee] = useState<EmployeeData | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [targetRole, setTargetRole] = useState(searchParams.get('target_role') || 'Senior Backend Developer');
  const [availableRoles, setAvailableRoles] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [generatingCareer, setGeneratingCareer] = useState(false);

  useEffect(() => {
    const init = async () => {
      if (!employeeId) return;
      setLoading(true);
      try {
        const [empRes, rolesRes] = await Promise.all([
          api.get(`/workforce/employees/${employeeId}`),
          api.get('/intelligence/role-requirements')
        ]);
        setEmployee(empRes.data);
        const rolesList = rolesRes.data.map((r: any) => r.role);
        setAvailableRoles(rolesList);

        const initialRole = searchParams.get('target_role') || (rolesList.length > 0 ? rolesList[0] : 'Senior Backend Developer');
        setTargetRole(initialRole);

        // Run or fetch analysis
        const analysisRes = await api.post('/intelligence/skill-gaps/analyze', {
          employee_id: employeeId,
          target_role: initialRole
        });
        setAnalysis(analysisRes.data);
      } catch (err) {
        console.error('Failed to load employee gap analysis', err);
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [employeeId]);

  const handleReanalyze = async (newRole: string) => {
    if (!employeeId || !newRole) return;
    setAnalyzing(true);
    setTargetRole(newRole);
    setSearchParams({ target_role: newRole });
    try {
      const res = await api.post('/intelligence/skill-gaps/analyze', {
        employee_id: employeeId,
        target_role: newRole
      });
      setAnalysis(res.data);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Analysis re-run failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleGenerateCareerPath = async () => {
    if (!employeeId || !targetRole) return;
    setGeneratingCareer(true);
    try {
      await api.post('/intelligence/career-paths/generate', {
        employee_id: employeeId,
        target_role: targetRole
      });
      navigate(`/dashboard/intelligence/career-paths?employee_id=${employeeId}`);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to generate career path');
    } finally {
      setGeneratingCareer(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 max-w-6xl mx-auto space-y-6">
        <div className="skeleton h-8 w-48 rounded-xl" />
        <div className="skeleton h-32 w-full rounded-2xl" />
        <div className="skeleton h-64 w-full rounded-2xl" />
      </div>
    );
  }

  if (!employee || !analysis) {
    return (
      <div className="p-8 max-w-6xl mx-auto text-center py-16">
        <AlertCircle className="w-12 h-12 mx-auto text-red-500 mb-3" />
        <h3 className="text-lg font-bold text-gray-900 dark:text-white">Analysis not found</h3>
        <Link to="/dashboard/intelligence/skill-gaps" className="text-sm text-indigo-600 dark:text-indigo-400 mt-2 inline-block">
          ← Back to Skill Gap Dashboard
        </Link>
      </div>
    );
  }

  const coverage = analysis.skill_coverage_score;
  const coverageColor = coverage >= 75 ? 'text-emerald-500' : coverage >= 50 ? 'text-amber-500' : 'text-rose-500';
  const coverageBadgeBg = coverage >= 75 ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300' : coverage >= 50 ? 'bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300' : 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300';

  return (
    <div className="p-6 lg:p-8 max-w-6xl mx-auto space-y-8 page-enter">
      {/* Back button & Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
        <Link to="/dashboard/intelligence/skill-gaps" className="hover:text-indigo-600 flex items-center gap-1">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Dashboard
        </Link>
        <span>/</span>
        <span className="font-semibold text-gray-700 dark:text-gray-300">{employee.name}</span>
      </div>

      {/* Employee Profile Header Card */}
      <div className="bg-white dark:bg-gray-800 rounded-3xl border border-gray-100 dark:border-gray-700 shadow-sm p-6 lg:p-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xl font-bold shadow-lg shadow-indigo-500/20 flex-shrink-0">
              {employee.name.split(' ').map(n => n[0]).join('')}
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{employee.name}</h2>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                  {employee.employee_id}
                </span>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                {employee.role} • {employee.department} • {employee.experience} yrs experience
              </p>
            </div>
          </div>

          {/* Supporting Performance Context (Not guaranteed promotion) */}
          <div className="flex items-center gap-4 bg-gray-50 dark:bg-gray-900/50 p-3.5 rounded-2xl border border-gray-100 dark:border-gray-800">
            <div className="text-center px-2">
              <p className="text-[10px] uppercase font-bold text-gray-400">Performance</p>
              <p className="text-lg font-bold text-gray-900 dark:text-white">{employee.performance_score} / 5.0</p>
            </div>
            <div className="h-8 w-px bg-gray-200 dark:bg-gray-700" />
            <div className="text-center px-2">
              <p className="text-[10px] uppercase font-bold text-gray-400">Engagement</p>
              <p className="text-lg font-bold text-gray-900 dark:text-white">{employee.engagement_score} / 5.0</p>
            </div>
          </div>
        </div>

        {/* Target Role Selector & Action Toolbar */}
        <div className="mt-8 pt-6 border-t border-gray-100 dark:border-gray-700 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3">
            <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Target Role Benchmark:
            </label>
            <div className="relative">
              <select
                value={targetRole}
                onChange={e => handleReanalyze(e.target.value)}
                disabled={analyzing}
                className="px-3.5 py-2 pr-8 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm font-semibold text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {availableRoles.map(r => (
                  <option key={r} value={r}>{r}</option>
                ))}
                {!availableRoles.includes(targetRole) && (
                  <option value={targetRole}>{targetRole}</option>
                )}
                <option value="Senior Backend Developer">Senior Backend Developer</option>
                <option value="Lead Software Engineer">Lead Software Engineer</option>
                <option value="Engineering Manager">Engineering Manager</option>
                <option value="Solutions Architect">Solutions Architect</option>
              </select>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleGenerateCareerPath}
              disabled={generatingCareer}
              className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-xl text-sm font-semibold shadow-md shadow-indigo-500/25 transition-all disabled:opacity-50"
            >
              <Compass className="w-4 h-4" />
              {generatingCareer ? 'Generating Career Path...' : 'View / Generate Career Path'}
            </button>
          </div>
        </div>
      </div>

      {/* Skill Coverage Score Banner */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Coverage Meter */}
        <div className="bg-white dark:bg-gray-800 rounded-3xl border border-gray-100 dark:border-gray-700 shadow-sm p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Calculated Skill Coverage</span>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${coverageBadgeBg}`}>
                {coverage >= 75 ? 'Strong Match' : coverage >= 50 ? 'Moderate Gap' : 'Substantial Gap'}
              </span>
            </div>
            <div className="mt-4 flex items-baseline gap-2">
              <span className={`text-5xl font-black tracking-tight ${coverageColor}`}>
                {coverage}%
              </span>
              <span className="text-xs text-gray-400 font-medium">overall match</span>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-gray-100 dark:border-gray-700/60">
            <div className="w-full bg-gray-100 dark:bg-gray-700 rounded-full h-2.5 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ${
                  coverage >= 75 ? 'bg-emerald-500' : coverage >= 50 ? 'bg-amber-500' : 'bg-rose-500'
                }`}
                style={{ width: `${coverage}%` }}
              />
            </div>
            <p className="text-[11px] text-gray-400 mt-2 leading-relaxed">
              Formula: (Matched Required Skills + 0.5 × Partial Skills) / Total Required Skills × 100
            </p>
          </div>
        </div>

        {/* Breakdown Counts */}
        <div className="md:col-span-2 bg-white dark:bg-gray-800 rounded-3xl border border-gray-100 dark:border-gray-700 shadow-sm p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-gray-900 dark:text-white mb-3">Requirements Breakdown</h3>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="p-4 rounded-2xl bg-emerald-50/70 dark:bg-emerald-950/30 border border-emerald-100 dark:border-emerald-900/40">
                <p className="text-xs font-semibold text-emerald-700 dark:text-emerald-300 uppercase">Matched</p>
                <p className="text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-1">{analysis.matched_count}</p>
                <p className="text-[11px] text-emerald-600/80 mt-0.5">Competencies satisfied</p>
              </div>

              <div className="p-4 rounded-2xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-100 dark:border-amber-900/40">
                <p className="text-xs font-semibold text-amber-700 dark:text-amber-300 uppercase">Skill Gaps</p>
                <p className="text-2xl font-black text-amber-600 dark:text-amber-400 mt-1">{analysis.missing_count}</p>
                <p className="text-[11px] text-amber-600/80 mt-0.5">Missing competencies</p>
              </div>

              <div className="p-4 rounded-2xl bg-blue-50/70 dark:bg-blue-950/30 border border-blue-100 dark:border-blue-900/40">
                <p className="text-xs font-semibold text-blue-700 dark:text-blue-300 uppercase">Partial</p>
                <p className="text-2xl font-black text-blue-600 dark:text-blue-400 mt-1">{analysis.partial_count}</p>
                <p className="text-[11px] text-blue-600/80 mt-0.5">Below required level</p>
              </div>
            </div>
          </div>

          {/* Ethics / Decision Support Disclaimer */}
          <div className="mt-4 p-3 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-100 dark:border-slate-800 flex items-start gap-2.5">
            <ShieldCheck className="w-4 h-4 text-indigo-500 mt-0.5 flex-shrink-0" />
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              <strong className="text-slate-700 dark:text-slate-200">Ethical Decision Support:</strong> Skill coverage represents capability alignment against target role benchmarks. It is advisory only and does not automatically trigger promotions or personnel actions.
            </p>
          </div>
        </div>
      </div>

      {/* Detailed Skill Comparison Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Matched Skills Card */}
        <div className="bg-white dark:bg-gray-800 rounded-3xl border border-gray-100 dark:border-gray-700 shadow-sm p-6 space-y-4">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-500" />
            <h3 className="font-bold text-gray-900 dark:text-white">Matched Skills ({analysis.matched_skills.length})</h3>
          </div>

          <div className="space-y-3">
            {analysis.matched_skills.map((item, i) => (
              <div key={i} className="p-3.5 rounded-xl bg-gray-50 dark:bg-gray-900/40 border border-gray-100 dark:border-gray-800">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-sm text-gray-900 dark:text-white">{item.skill}</span>
                  <span className="text-xs px-2 py-0.5 rounded-md font-semibold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300">
                    Matched
                  </span>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{item.explanation}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Skill Gaps Card */}
        <div className="bg-white dark:bg-gray-800 rounded-3xl border border-gray-100 dark:border-gray-700 shadow-sm p-6 space-y-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            <h3 className="font-bold text-gray-900 dark:text-white">Identified Skill Gaps ({analysis.missing_skills.length})</h3>
          </div>

          <div className="space-y-3">
            {analysis.missing_skills.map((item, i) => (
              <div key={i} className="p-3.5 rounded-xl bg-gray-50 dark:bg-gray-900/40 border border-gray-100 dark:border-gray-800">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-sm text-gray-900 dark:text-white">{item.skill}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-md font-semibold ${
                    item.status === 'MISSING'
                      ? 'bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300'
                      : 'bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300'
                  }`}>
                    {item.status === 'MISSING' ? 'Required Gap' : 'Preferred'}
                  </span>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{item.explanation}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Explainable Development Recommendations */}
      <div className="bg-white dark:bg-gray-800 rounded-3xl border border-gray-100 dark:border-gray-700 shadow-sm p-6 lg:p-8 space-y-5">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">Explainable Development Recommendations</h3>
            </div>
            <p className="text-xs text-gray-400 mt-1">
              Data-backed learning paths explaining exactly why each competency is recommended
            </p>
          </div>
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 border border-purple-100 dark:border-purple-800">
            Explainable AI
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {analysis.recommended_development_areas.map((rec, i) => (
            <div key={i} className="p-4 rounded-2xl bg-gray-50 dark:bg-gray-900/50 border border-gray-100 dark:border-gray-800 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-sm text-gray-900 dark:text-white">{rec.recommendation}</span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                    rec.priority === 'HIGH' ? 'bg-red-100 text-red-700 dark:bg-red-950/50 dark:text-red-300' : 'bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300'
                  }`}>
                    {rec.priority} Priority
                  </span>
                </div>
                <div className="p-2.5 rounded-xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 text-xs text-gray-600 dark:text-gray-300 leading-relaxed">
                  <strong className="text-indigo-600 dark:text-indigo-400 font-semibold">Why recommended: </strong>
                  {rec.reason}
                </div>
              </div>
              <div className="mt-3 flex items-center justify-between text-xs text-gray-400 pt-2 border-t border-gray-200/50 dark:border-gray-700/50">
                <span className="uppercase text-[10px] font-bold">Type: {rec.recommendation_type}</span>
                <span className="font-medium text-gray-600 dark:text-gray-300">Skill: {rec.skill}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
