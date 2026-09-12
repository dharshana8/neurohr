import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../lib/api';
import {
  Brain, Users, Target, AlertTriangle,
  Plus, ArrowRight, Layers, BookOpen
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';

interface Analytics {
  total_employees_analyzed: number;
  average_skill_coverage: number;
  top_skill_gaps: { skill: string; count: number }[];
  department_breakdown: { department: string; avg_coverage: number; analyzed_count: number }[];
  role_breakdown: { role: string; avg_coverage: number; analyzed_count: number }[];
}

interface Employee {
  id: string;
  employee_id: string;
  name: string;
  department: string;
  role: string;
  skills: string;
}

interface RoleRequirement {
  id: string;
  requirement_id: string;
  role: string;
  required_skills: string[];
  preferred_skills: string[];
}

interface SkillItem {
  id: string;
  skill_id: string;
  name: string;
  category: string;
  aliases: string[];
}

export default function SkillGapDashboard() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'overview' | 'requirements' | 'taxonomy'>('overview');
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [roles, setRoles] = useState<RoleRequirement[]>([]);
  const [skills, setSkills] = useState<SkillItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal State
  const [showAnalyzeModal, setShowAnalyzeModal] = useState(false);
  const [selectedEmpId, setSelectedEmpId] = useState('');
  const [selectedTargetRole, setSelectedTargetRole] = useState('');
  const [analyzing, setAnalyzing] = useState(false);

  // Create Role Requirement Modal State
  const [showRoleModal, setShowRoleModal] = useState(false);
  const [newRoleName, setNewRoleName] = useState('');
  const [newRequiredSkills, setNewRequiredSkills] = useState('');
  const [newPreferredSkills, setNewPreferredSkills] = useState('');

  // Create Skill Modal State
  const [showSkillModal, setShowSkillModal] = useState(false);
  const [newSkillName, setNewSkillName] = useState('');
  const [newSkillCategory, setNewSkillCategory] = useState('General');
  const [newSkillAliases, setNewSkillAliases] = useState('');

  const loadData = async () => {
    setLoading(true);
    try {
      const [analyticsRes, empRes, rolesRes, skillsRes] = await Promise.allSettled([
        api.get('/intelligence/skill-gaps/analytics'),
        api.get('/workforce/employees'),
        api.get('/intelligence/role-requirements'),
        api.get('/intelligence/skills')
      ]);

      if (analyticsRes.status === 'fulfilled') setAnalytics(analyticsRes.value.data);
      if (empRes.status === 'fulfilled') setEmployees(empRes.value.data);
      if (rolesRes.status === 'fulfilled') setRoles(rolesRes.value.data);
      if (skillsRes.status === 'fulfilled') setSkills(skillsRes.value.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRunAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEmpId || !selectedTargetRole) return;
    setAnalyzing(true);
    try {
      await api.post('/intelligence/skill-gaps/analyze', {
        employee_id: selectedEmpId,
        target_role: selectedTargetRole
      });
      setShowAnalyzeModal(false);
      navigate(`/dashboard/intelligence/skill-gaps/${selectedEmpId}?target_role=${encodeURIComponent(selectedTargetRole)}`);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleCreateRoleRequirement = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/intelligence/role-requirements', {
        role: newRoleName,
        required_skills: newRequiredSkills.split(',').map(s => s.trim()).filter(Boolean),
        preferred_skills: newPreferredSkills.split(',').map(s => s.trim()).filter(Boolean),
        skill_levels: {}
      });
      setShowRoleModal(false);
      setNewRoleName('');
      setNewRequiredSkills('');
      setNewPreferredSkills('');
      loadData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to create role requirement');
    }
  };

  const handleCreateSkill = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/intelligence/skills', {
        name: newSkillName,
        category: newSkillCategory,
        aliases: newSkillAliases.split(',').map(s => s.trim()).filter(Boolean)
      });
      setShowSkillModal(false);
      setNewSkillName('');
      setNewSkillAliases('');
      loadData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to create skill');
    }
  };

  const hasData = analytics && analytics.total_employees_analyzed > 0;

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-8 page-enter">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Skill Gap Analysis</h2>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300">
              Intelligence
            </span>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Compare workforce capabilities against role benchmarks to reveal targeted growth opportunities.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowAnalyzeModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-medium shadow-md shadow-indigo-500/25 transition-all"
          >
            <Brain className="w-4 h-4" />
            Analyze Employee
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-100 dark:border-gray-700 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Analyzed Employees</p>
            <div className="p-2 rounded-xl bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-bold text-gray-900 dark:text-white">
            {loading ? '—' : analytics?.total_employees_analyzed ?? 0}
          </p>
          <p className="text-xs text-gray-400 mt-1">Profile benchmark runs</p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-100 dark:border-gray-700 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Avg Skill Coverage</p>
            <div className="p-2 rounded-xl bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400">
              <Target className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-bold text-gray-900 dark:text-white">
            {loading ? '—' : hasData ? `${analytics?.average_skill_coverage}%` : '—'}
          </p>
          <p className="text-xs text-gray-400 mt-1">Overall readiness match</p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-100 dark:border-gray-700 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Configured Roles</p>
            <div className="p-2 rounded-xl bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400">
              <Layers className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-bold text-gray-900 dark:text-white">
            {loading ? '—' : roles.length}
          </p>
          <p className="text-xs text-gray-400 mt-1">Target benchmarks set</p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-100 dark:border-gray-700 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Skill Taxonomy</p>
            <div className="p-2 rounded-xl bg-amber-50 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400">
              <BookOpen className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-bold text-gray-900 dark:text-white">
            {loading ? '—' : skills.length}
          </p>
          <p className="text-xs text-gray-400 mt-1">Recognized competencies</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-gray-200 dark:border-gray-800 pb-1">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all ${
            activeTab === 'overview'
              ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          Workforce Directory & Analysis
        </button>
        <button
          onClick={() => setActiveTab('requirements')}
          className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all ${
            activeTab === 'requirements'
              ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          Role Benchmarks ({roles.length})
        </button>
        <button
          onClick={() => setActiveTab('taxonomy')}
          className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all ${
            activeTab === 'taxonomy'
              ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          Skill Taxonomy ({skills.length})
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Top Skill Gaps & Dept breakdown */}
          {hasData ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Top Gaps Card */}
              <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-6">
                <h3 className="text-base font-bold text-gray-900 dark:text-white mb-1">Most Common Skill Gaps</h3>
                <p className="text-xs text-gray-400 mb-4">Competencies most frequently missing or partial</p>
                <div className="space-y-3">
                  {analytics?.top_skill_gaps.map(g => (
                    <div key={g.skill} className="flex items-center justify-between p-3 rounded-xl bg-gray-50 dark:bg-gray-900/50">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-amber-500" />
                        <span className="text-sm font-medium text-gray-800 dark:text-gray-200">{g.skill}</span>
                      </div>
                      <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300">
                        {g.count} gaps
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Department Readiness Chart */}
              <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-6">
                <h3 className="text-base font-bold text-gray-900 dark:text-white mb-1">Skill Coverage by Department</h3>
                <p className="text-xs text-gray-400 mb-4">Average readiness match across departments</p>
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={analytics?.department_breakdown || []}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                      <XAxis dataKey="department" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} domain={[0, 100]} />
                      <Tooltip
                        contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 12, color: '#f8fafc', fontSize: 12 }}
                        formatter={(v: any) => [`${v}%`, 'Avg Coverage']}
                      />
                      <Bar dataKey="avg_coverage" fill="#6366f1" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-6 rounded-2xl bg-indigo-50/60 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800 flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-indigo-900 dark:text-indigo-200">No sufficient analytics data available yet</p>
                <p className="text-xs text-indigo-700 dark:text-indigo-400 mt-0.5">
                  Select an employee below to perform an instant skill gap analysis against any target role.
                </p>
              </div>
              <button
                onClick={() => setShowAnalyzeModal(true)}
                className="px-3.5 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-semibold shadow-sm"
              >
                Analyze Now
              </button>
            </div>
          )}

          {/* Employees List Table */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm overflow-hidden">
            <div className="p-5 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-gray-900 dark:text-white">Workforce Competency Roster</h3>
                <p className="text-xs text-gray-400 mt-0.5">Click an employee to view detailed skill breakdown and career roadmap</p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-gray-50/75 dark:bg-gray-900/50 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-3.5">Employee</th>
                    <th className="px-6 py-3.5">Department</th>
                    <th className="px-6 py-3.5">Current Role</th>
                    <th className="px-6 py-3.5">Recorded Skills</th>
                    <th className="px-6 py-3.5 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700/60">
                  {employees.map(emp => (
                    <tr key={emp.employee_id} className="hover:bg-gray-50/50 dark:hover:bg-gray-900/30 transition-colors">
                      <td className="px-6 py-4 font-semibold text-gray-900 dark:text-white">
                        {emp.name}
                        <span className="block text-xs font-normal text-gray-400">{emp.employee_id}</span>
                      </td>
                      <td className="px-6 py-4 text-gray-600 dark:text-gray-300">{emp.department}</td>
                      <td className="px-6 py-4 text-gray-600 dark:text-gray-300">{emp.role}</td>
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-1 max-w-md">
                          {emp.skills.split(',').slice(0, 4).map(s => (
                            <span key={s} className="px-2 py-0.5 rounded-md bg-gray-100 dark:bg-gray-700 text-[11px] font-medium text-gray-700 dark:text-gray-300">
                              {s.trim()}
                            </span>
                          ))}
                          {emp.skills.split(',').length > 4 && (
                            <span className="text-xs text-gray-400 self-center">
                              +{emp.skills.split(',').length - 4} more
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => {
                            setSelectedEmpId(emp.employee_id);
                            setShowAnalyzeModal(true);
                          }}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-900/50 text-xs font-semibold transition-all"
                        >
                          Analyze Gap
                          <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Role Benchmarks Tab */}
      {activeTab === 'requirements' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-gray-900 dark:text-white">Role Skill Requirements</h3>
              <p className="text-xs text-gray-400">Define benchmarks for required and preferred competencies per position</p>
            </div>
            <button
              onClick={() => setShowRoleModal(true)}
              className="flex items-center gap-2 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-sm transition-all"
            >
              <Plus className="w-4 h-4" />
              Add Role Benchmark
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {roles.map(r => (
              <div key={r.requirement_id} className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-5 space-y-4">
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="font-bold text-gray-900 dark:text-white">{r.role}</h4>
                    <span className="text-[11px] text-gray-400">Standard Requirement</span>
                  </div>
                  <span className="px-2 py-0.5 rounded-md bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 text-xs font-medium">
                    {r.required_skills.length} Required
                  </span>
                </div>

                <div>
                  <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1.5 uppercase tracking-wider">Required Skills</p>
                  <div className="flex flex-wrap gap-1.5">
                    {r.required_skills.map(s => (
                      <span key={s} className="px-2 py-1 rounded-md bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 text-xs font-medium">
                        ✓ {s}
                      </span>
                    ))}
                  </div>
                </div>

                {r.preferred_skills.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1.5 uppercase tracking-wider">Preferred Skills</p>
                    <div className="flex flex-wrap gap-1.5">
                      {r.preferred_skills.map(s => (
                        <span key={s} className="px-2 py-1 rounded-md bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs font-medium">
                          + {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Skill Taxonomy Tab */}
      {activeTab === 'taxonomy' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-gray-900 dark:text-white">Competency Taxonomy</h3>
              <p className="text-xs text-gray-400">Normalized dictionary of skills with multi-alias recognition</p>
            </div>
            <button
              onClick={() => setShowSkillModal(true)}
              className="flex items-center gap-2 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-sm transition-all"
            >
              <Plus className="w-4 h-4" />
              Add Skill
            </button>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50/75 dark:bg-gray-900/50 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3.5">Canonical Skill</th>
                  <th className="px-6 py-3.5">Category</th>
                  <th className="px-6 py-3.5">Normalized Aliases</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700/60">
                {skills.map(s => (
                  <tr key={s.skill_id} className="hover:bg-gray-50/50 dark:hover:bg-gray-900/30">
                    <td className="px-6 py-3.5 font-semibold text-gray-900 dark:text-white">{s.name}</td>
                    <td className="px-6 py-3.5">
                      <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                        {s.category}
                      </span>
                    </td>
                    <td className="px-6 py-3.5 text-gray-500 dark:text-gray-400">
                      {s.aliases.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {s.aliases.map(a => (
                            <span key={a} className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-[11px]">
                              {a}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-xs text-gray-400 italic">None</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal: Run Skill Gap Analysis */}
      {showAnalyzeModal && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl max-w-md w-full p-6 shadow-xl border border-gray-100 dark:border-gray-700 space-y-5 animate-in fade-in">
            <div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">Run Skill Gap Analysis</h3>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                Select an employee and the target role benchmark to analyze capability coverage.
              </p>
            </div>

            <form onSubmit={handleRunAnalysis} className="space-y-4">
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
                  Target Role
                </label>
                <input
                  type="text"
                  list="target-roles-list"
                  value={selectedTargetRole}
                  onChange={e => setSelectedTargetRole(e.target.value)}
                  placeholder="e.g. Senior Backend Developer"
                  required
                  className="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <datalist id="target-roles-list">
                  {roles.map(r => (
                    <option key={r.role} value={r.role} />
                  ))}
                  <option value="Senior Backend Developer" />
                  <option value="Lead Software Engineer" />
                  <option value="Full Stack Architect" />
                  <option value="Engineering Manager" />
                </datalist>
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAnalyzeModal(false)}
                  className="px-4 py-2 rounded-xl text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={analyzing}
                  className="px-5 py-2 rounded-xl text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 shadow-md shadow-indigo-500/25 transition-all disabled:opacity-50"
                >
                  {analyzing ? 'Analyzing...' : 'Generate Analysis'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Create Role Benchmark */}
      {showRoleModal && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl max-w-md w-full p-6 shadow-xl border border-gray-100 dark:border-gray-700 space-y-5">
            <div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">Add Role Benchmark</h3>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                Set required and preferred skills for automated gap calculations.
              </p>
            </div>

            <form onSubmit={handleCreateRoleRequirement} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Role Title
                </label>
                <input
                  type="text"
                  value={newRoleName}
                  onChange={e => setNewRoleName(e.target.value)}
                  placeholder="e.g. Senior Backend Developer"
                  required
                  className="w-full px-3.5 py-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Required Skills (comma separated)
                </label>
                <input
                  type="text"
                  value={newRequiredSkills}
                  onChange={e => setNewRequiredSkills(e.target.value)}
                  placeholder="e.g. Python, FastAPI, MongoDB"
                  required
                  className="w-full px-3.5 py-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Preferred Skills (comma separated)
                </label>
                <input
                  type="text"
                  value={newPreferredSkills}
                  onChange={e => setNewPreferredSkills(e.target.value)}
                  placeholder="e.g. Docker, AWS, Kubernetes"
                  className="w-full px-3.5 py-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm"
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowRoleModal(false)}
                  className="px-4 py-2 rounded-xl text-sm font-medium text-gray-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700"
                >
                  Save Benchmark
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Add Skill to Taxonomy */}
      {showSkillModal && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl max-w-md w-full p-6 shadow-xl border border-gray-100 dark:border-gray-700 space-y-5">
            <div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">Add Skill to Taxonomy</h3>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                Register a new canonical skill with synonymous aliases for normalization.
              </p>
            </div>

            <form onSubmit={handleCreateSkill} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Canonical Skill Name
                </label>
                <input
                  type="text"
                  value={newSkillName}
                  onChange={e => setNewSkillName(e.target.value)}
                  placeholder="e.g. GraphQL"
                  required
                  className="w-full px-3.5 py-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Category
                </label>
                <select
                  value={newSkillCategory}
                  onChange={e => setNewSkillCategory(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm"
                >
                  <option value="Backend">Backend</option>
                  <option value="Frontend">Frontend</option>
                  <option value="DevOps">DevOps</option>
                  <option value="Cloud">Cloud</option>
                  <option value="Database">Database</option>
                  <option value="AI/ML">AI/ML</option>
                  <option value="Soft Skills">Soft Skills</option>
                  <option value="General">General</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Aliases (comma separated)
                </label>
                <input
                  type="text"
                  value={newSkillAliases}
                  onChange={e => setNewSkillAliases(e.target.value)}
                  placeholder="e.g. gql, graphql-api"
                  className="w-full px-3.5 py-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm"
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowSkillModal(false)}
                  className="px-4 py-2 rounded-xl text-sm font-medium text-gray-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700"
                >
                  Save Skill
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
