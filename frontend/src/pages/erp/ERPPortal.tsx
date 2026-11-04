import { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Briefcase, Layers, Cpu, Database, RefreshCw, CheckCircle2,
  AlertTriangle, DollarSign, Laptop, Users, ArrowUpRight, ShieldCheck, Play,
  UserPlus, Trash2, X
} from 'lucide-react';

interface ProjectMember {
  id: string;
  employee_id: string;
  name: string;
  role: string;
  department: string;
  billability_pct: number;
  attrition_risk?: number;
  risk_level?: string;
}

interface ERPProject {
  id: string;
  name: string;
  client: string;
  budget: number;
  spent: number;
  target_deadline: string;
  headcount_required: number;
  headcount_allocated: number;
  health: string;
  staffing_gap: number;
  critical_skills_needed: string[];
  members?: ProjectMember[];
}

export default function ERPPortal() {
  const [activeTab, setActiveTab] = useState<'projects' | 'resources' | 'budgets' | 'assets' | 'sync'>('projects');
  const [projects, setProjects] = useState<ERPProject[]>([]);
  const [resourceData, setResourceData] = useState<any>(null);
  const [budgets, setBudgets] = useState<any>(null);
  const [assets, setAssets] = useState<any[]>([]);
  const [syncStatus, setSyncStatus] = useState<any>(null);
  const [syncing, setSyncing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [selectedProjectForAdd, setSelectedProjectForAdd] = useState<any>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [allEmployees, setAllEmployees] = useState<any[]>([]);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchERPData();
  }, []);

  const fetchERPData = async () => {
    try {
      const [pRes, rRes, bRes, aRes, eRes] = await Promise.all([
        axios.get('http://localhost:8000/api/v1/erp/projects').catch(() => ({ data: [] })),
        axios.get('http://localhost:8000/api/v1/erp/resources').catch(() => ({ data: null })),
        axios.get('http://localhost:8000/api/v1/erp/budgets').catch(() => ({ data: null })),
        axios.get('http://localhost:8000/api/v1/erp/assets').catch(() => ({ data: [] })),
        axios.get('http://localhost:8000/api/v1/workforce/employees').catch(() => ({ data: [] }))
      ]);
      setProjects(pRes.data);
      setResourceData(rRes.data);
      setBudgets(bRes.data);
      setAssets(aRes.data);
      setAllEmployees(eRes.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleAddMember = async (projectId: string, employeeId: string) => {
    try {
      await axios.post(`http://localhost:8000/api/v1/erp/projects/${projectId}/members`, { employee_id: employeeId });
      setActionMessage("Successfully assigned employee to project!");
      setTimeout(() => setActionMessage(null), 3000);
      setShowAddModal(false);
      fetchERPData();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to add member");
    }
  };

  const handleRemoveMember = async (projectId: string, employeeId: string) => {
    if (!window.confirm("Remove this employee from the project team and move them back to the bench?")) return;
    try {
      await axios.delete(`http://localhost:8000/api/v1/erp/projects/${projectId}/members/${employeeId}`);
      setActionMessage("Employee moved to Bench.");
      setTimeout(() => setActionMessage(null), 3000);
      fetchERPData();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to remove member");
    }
  };

  const handleTriggerSync = async () => {
    setSyncing(true);
    try {
      const res = await axios.post('http://localhost:8000/api/v1/erp/sync');
      setSyncStatus(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-2">
            ⚙️ Enterprise Resource Planning
          </div>
          <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight">
            ERP Operations & Resource Portal
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Tracking project headcount, client billability, departmental cost centers, and cross-system sync.
          </p>
        </div>

        <button
          onClick={handleTriggerSync}
          disabled={syncing}
          className="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-sm font-semibold shadow-md shadow-emerald-500/25 transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
          {syncing ? 'Synchronizing HRIS & ERP...' : 'Trigger Bi-Directional Sync'}
        </button>
      </div>

      {actionMessage && (
        <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300 rounded-xl text-xs font-semibold flex items-center gap-2 animate-in fade-in">
          <CheckCircle2 className="w-4 h-4" />
          <span>{actionMessage}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-gray-200 dark:border-gray-800 gap-6 overflow-x-auto">
        <button
          onClick={() => setActiveTab('projects')}
          className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 whitespace-nowrap transition-all ${
            activeTab === 'projects'
              ? 'border-emerald-600 text-emerald-600 dark:text-emerald-400'
              : 'border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-gray-200'
          }`}
        >
          <Briefcase className="w-4 h-4" />
          Projects & Headcount ({projects.length})
        </button>
        <button
          onClick={() => setActiveTab('resources')}
          className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 whitespace-nowrap transition-all ${
            activeTab === 'resources'
              ? 'border-emerald-600 text-emerald-600 dark:text-emerald-400'
              : 'border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-gray-200'
          }`}
        >
          <Users className="w-4 h-4" />
          Bench & Billability
        </button>
        <button
          onClick={() => setActiveTab('budgets')}
          className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 whitespace-nowrap transition-all ${
            activeTab === 'budgets'
              ? 'border-emerald-600 text-emerald-600 dark:text-emerald-400'
              : 'border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-gray-200'
          }`}
        >
          <DollarSign className="w-4 h-4" />
          Cost Centers & Ledger
        </button>
        <button
          onClick={() => setActiveTab('assets')}
          className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 whitespace-nowrap transition-all ${
            activeTab === 'assets'
              ? 'border-emerald-600 text-emerald-600 dark:text-emerald-400'
              : 'border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-gray-200'
          }`}
        >
          <Laptop className="w-4 h-4" />
          IT Assets & Software Seats
        </button>
        <button
          onClick={() => setActiveTab('sync')}
          className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 whitespace-nowrap transition-all ${
            activeTab === 'sync'
              ? 'border-emerald-600 text-emerald-600 dark:text-emerald-400'
              : 'border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-gray-200'
          }`}
        >
          <RefreshCw className="w-4 h-4" />
          Integration Middleware Status
        </button>
      </div>

      {/* Tab: Projects */}
      {activeTab === 'projects' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white dark:bg-gray-800 p-5 rounded-2xl border border-gray-100 dark:border-gray-700">
              <span className="text-xs font-semibold text-gray-400 uppercase">Active Projects</span>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{projects.length}</p>
            </div>
            <div className="bg-white dark:bg-gray-800 p-5 rounded-2xl border border-gray-100 dark:border-gray-700">
              <span className="text-xs font-semibold text-red-500 uppercase">Staffing Deficits</span>
              <p className="text-2xl font-bold text-red-600 mt-1">
                {projects.reduce((acc, p) => acc + p.staffing_gap, 0)} Engineers
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 p-5 rounded-2xl border border-gray-100 dark:border-gray-700">
              <span className="text-xs font-semibold text-emerald-500 uppercase">Total CapEx Budget</span>
              <p className="text-2xl font-bold text-emerald-600 mt-1">
                ₹{projects.reduce((acc, p) => acc + p.budget, 0).toLocaleString('en-IN')}
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 p-5 rounded-2xl border border-gray-100 dark:border-gray-700">
              <span className="text-xs font-semibold text-purple-500 uppercase">Overall Health</span>
              <p className="text-2xl font-bold text-purple-600 mt-1">87.5% On Schedule</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {projects.map(proj => {
              const pctSpent = Math.round((proj.spent / proj.budget) * 100);
              return (
                <div key={proj.id} className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-6 space-y-4 shadow-sm">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-widest">{proj.id} &bull; {proj.client}</span>
                      <h3 className="text-lg font-bold text-gray-900 dark:text-white mt-0.5">{proj.name}</h3>
                    </div>
                    <span className={`px-2.5 py-0.5 text-xs font-bold rounded-full ${
                      proj.health === 'HEALTHY' ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600' :
                      proj.health === 'WARNING' ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-600' :
                      'bg-red-100 dark:bg-red-900/30 text-red-600'
                    }`}>
                      {proj.health}
                    </span>
                  </div>

                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>Budget Burn (₹{proj.spent.toLocaleString('en-IN')} / ₹{proj.budget.toLocaleString('en-IN')})</span>
                      <span className="font-semibold text-gray-800 dark:text-gray-200">{pctSpent}%</span>
                    </div>
                    <div className="w-full h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div className={`h-full ${pctSpent > 80 ? 'bg-amber-500' : 'bg-emerald-500'}`} style={{ width: `${pctSpent}%` }} />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3 pt-2 text-xs">
                    <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded-xl">
                      <span className="text-gray-400">Headcount Needed</span>
                      <p className="text-base font-bold text-gray-900 dark:text-white mt-0.5">
                        {proj.headcount_allocated} / {proj.headcount_required} Members
                      </p>
                    </div>
                    <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded-xl">
                      <span className="text-gray-400">Target Go-Live</span>
                      <p className="text-base font-bold text-gray-900 dark:text-white mt-0.5">
                        {proj.target_deadline}
                      </p>
                    </div>
                  </div>

                  {proj.staffing_gap > 0 && (
                    <div className="p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/40 rounded-xl text-xs space-y-1">
                      <div className="flex items-center gap-1.5 font-bold text-red-700 dark:text-red-400">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        <span>Staffing Gap: {proj.staffing_gap} open roles!</span>
                      </div>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {proj.critical_skills_needed.map(skill => (
                          <span key={skill} className="px-2 py-0.5 bg-white dark:bg-gray-800 rounded text-[10px] text-red-600 dark:text-red-300 border border-red-200 dark:border-red-800">
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Project Team Members Roster */}
                  <div className="pt-3 border-t border-gray-100 dark:border-gray-700/60 space-y-2.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-gray-700 dark:text-gray-300 flex items-center gap-1.5">
                        <Users className="w-3.5 h-3.5 text-indigo-500" />
                        Assigned Team ({proj.members?.length || 0})
                      </span>
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedProjectForAdd(proj);
                          setShowAddModal(true);
                        }}
                        className="px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-950/40 dark:hover:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800 rounded-lg text-xs font-semibold flex items-center gap-1 transition"
                      >
                        <UserPlus className="w-3.5 h-3.5" />
                        + Add Member
                      </button>
                    </div>

                    {proj.members && proj.members.length > 0 ? (
                      <div className="space-y-1.5 max-h-44 overflow-y-auto pr-1">
                        {proj.members.map((m: any) => (
                          <div key={m.id} className="p-2 rounded-xl bg-gray-50 dark:bg-gray-700/30 border border-gray-100 dark:border-gray-700/50 flex items-center justify-between text-xs hover:border-indigo-200 transition">
                            <div className="flex items-center gap-2">
                              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white flex items-center justify-center text-[10px] font-bold flex-shrink-0">
                                {m.name.slice(0, 2).toUpperCase()}
                              </div>
                              <div>
                                <p className="font-semibold text-gray-900 dark:text-white leading-tight">{m.name}</p>
                                <p className="text-[10px] text-gray-400">{m.role} &bull; {m.department}</p>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                                m.risk_level === 'HIGH' ? 'bg-red-100 text-red-600 dark:bg-red-950/50' : 'bg-emerald-100 text-emerald-600 dark:bg-emerald-950/50'
                              }`}>
                                {Math.round((m.attrition_risk || 0.15) * 100)}% Risk
                              </span>
                              <button
                                type="button"
                                onClick={() => handleRemoveMember(proj.id, m.id)}
                                title="Remove employee from project and move to bench"
                                className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/40 rounded transition"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-400 italic py-1.5">No members currently assigned to this project.</p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Tab: Resources & Bench */}
      {activeTab === 'resources' && resourceData && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-6 bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700">
              <span className="text-xs text-gray-400">Average Workforce Billability</span>
              <p className="text-3xl font-extrabold text-emerald-600 mt-2">{resourceData.avg_billability_pct}%</p>
            </div>
            <div className="p-6 bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700">
              <span className="text-xs text-gray-400">Fully Allocated On Client Projects</span>
              <p className="text-3xl font-extrabold text-gray-900 dark:text-white mt-2">{resourceData.allocated_count} Staff</p>
            </div>
            <div className="p-6 bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700">
              <span className="text-xs text-gray-400">Available on Bench (Ready to Deploy)</span>
              <p className="text-3xl font-extrabold text-amber-500 mt-2">{resourceData.bench_count} Engineers</p>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-6 shadow-sm">
            <h3 className="font-bold text-gray-900 dark:text-white mb-4">Unallocated Bench Workforce</h3>
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {resourceData.bench_list.map((emp: any) => (
                <div key={emp.id} className="py-4 flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-white">{emp.name}</h4>
                    <p className="text-xs text-gray-500">{emp.role} &bull; {emp.department} &bull; Salary: ₹{emp.salary.toLocaleString('en-IN')}</p>
                  </div>
                  <button className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold">
                    Allocate to Project Titan
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab: Budgets */}
      {activeTab === 'budgets' && budgets && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="p-5 bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700">
              <span className="text-xs text-gray-400">Total Approved Budget</span>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">₹{budgets.summary.total_allocated.toLocaleString('en-IN')}</p>
            </div>
            <div className="p-5 bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700">
              <span className="text-xs text-gray-400">Payroll Spend (HRIS Synced)</span>
              <p className="text-2xl font-bold text-indigo-600 mt-1">₹{budgets.summary.total_payroll.toLocaleString('en-IN')}</p>
            </div>
            <div className="p-5 bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700">
              <span className="text-xs text-gray-400">Operating Expenses</span>
              <p className="text-2xl font-bold text-emerald-600 mt-1">₹{budgets.summary.total_operational.toLocaleString('en-IN')}</p>
            </div>
            <div className="p-5 bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700">
              <span className="text-xs text-gray-400">Cumulative Burn Rate</span>
              <p className="text-2xl font-bold text-purple-600 mt-1">{budgets.summary.burn_rate_pct}%</p>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-50 dark:bg-gray-900 text-gray-500 uppercase border-b border-gray-200 dark:border-gray-700">
                <tr>
                  <th className="px-6 py-3">Cost Center</th>
                  <th className="px-6 py-3">Department</th>
                  <th className="px-6 py-3">Allocated</th>
                  <th className="px-6 py-3">Payroll Expense</th>
                  <th className="px-6 py-3">Operations</th>
                  <th className="px-6 py-3">Burn %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700 text-gray-800 dark:text-gray-200 font-medium">
                {budgets.cost_centers.map((cc: any) => (
                  <tr key={cc.code} className="hover:bg-gray-50/50 dark:hover:bg-gray-800/50">
                    <td className="px-6 py-4 font-mono font-bold text-indigo-600 dark:text-indigo-400">{cc.code}</td>
                    <td className="px-6 py-4">{cc.department}</td>
                    <td className="px-6 py-4">₹{cc.allocated_budget.toLocaleString('en-IN')}</td>
                    <td className="px-6 py-4">₹{cc.payroll_expenses.toLocaleString('en-IN')}</td>
                    <td className="px-6 py-4">₹{cc.operational_expenses.toLocaleString('en-IN')}</td>
                    <td className="px-6 py-4 font-bold">{cc.burn_rate_pct}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab: Assets */}
      {activeTab === 'assets' && (
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 overflow-hidden shadow-sm">
          <table className="w-full text-left text-xs">
            <thead className="bg-gray-50 dark:bg-gray-900 text-gray-500 uppercase border-b border-gray-200 dark:border-gray-700">
              <tr>
                <th className="px-6 py-3">Asset Tag</th>
                <th className="px-6 py-3">Category</th>
                <th className="px-6 py-3">Item Name</th>
                <th className="px-6 py-3">Assigned Employee</th>
                <th className="px-6 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700 text-gray-800 dark:text-gray-200 font-medium">
              {assets.map((a: any) => (
                <tr key={a.asset_tag} className="hover:bg-gray-50/50 dark:hover:bg-gray-800/50">
                  <td className="px-6 py-4 font-mono font-bold text-emerald-600 dark:text-emerald-400">{a.asset_tag}</td>
                  <td className="px-6 py-4">{a.type}</td>
                  <td className="px-6 py-4 font-semibold">{a.item}</td>
                  <td className="px-6 py-4">{a.assigned_name} ({a.assigned_to})</td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 font-bold text-[10px]">
                      {a.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab: Sync Middleware */}
      {activeTab === 'sync' && (
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-6 space-y-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">HRIS & ERP Integration Middleware</h3>
              <p className="text-xs text-gray-500">Autonomous synchronization pipeline between People Data and Enterprise Ledger</p>
            </div>
            <button
              onClick={handleTriggerSync}
              disabled={syncing}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold flex items-center gap-2"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
              Run Sync Now
            </button>
          </div>

          <div className="space-y-4">
            <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                <div>
                  <h4 className="text-sm font-bold text-gray-900 dark:text-white">HRIS Payroll ➔ ERP Financial General Ledger</h4>
                  <p className="text-xs text-gray-400">Syncs salary disbursements and tax deductions to cost centers</p>
                </div>
              </div>
              <span className="text-xs font-mono text-emerald-500 font-bold">100% Synced (₹0.00 Variance)</span>
            </div>

            <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                <div>
                  <h4 className="text-sm font-bold text-gray-900 dark:text-white">ERP Project Gaps ➔ HRIS Recruitment Pipeline</h4>
                  <p className="text-xs text-gray-400">Generates requisitions for staffing deficits automatically</p>
                </div>
              </div>
              <span className="text-xs font-mono text-indigo-500 font-bold">2 Requisitions Created</span>
            </div>

            <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                <div>
                  <h4 className="text-sm font-bold text-gray-900 dark:text-white">Employee Onboarding ➔ IT Asset Provisioning</h4>
                  <p className="text-xs text-gray-400">Auto-triggers laptop dispatch and IDE licenses upon contract sign</p>
                </div>
              </div>
              <span className="text-xs font-mono text-purple-500 font-bold">Automated Webhook Active</span>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Add Team Member to Project */}
      {showAddModal && selectedProjectForAdd && (
        <div 
          className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm"
          onClick={() => setShowAddModal(false)}
        >
          <div 
            className="bg-white dark:bg-gray-900 rounded-3xl max-w-xl w-full border border-gray-100 dark:border-gray-800 shadow-2xl p-6 space-y-4 animate-in fade-in zoom-in-95 duration-200 relative max-h-[85vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 border-b border-gray-100 dark:border-gray-800">
              <div>
                <h3 className="text-base font-bold text-gray-900 dark:text-white">
                  Add Member to {selectedProjectForAdd.name}
                </h3>
                <p className="text-xs text-gray-400 mt-0.5">
                  Select an available or bench employee to assign to this project deliverable.
                </p>
              </div>
              <button
                onClick={() => setShowAddModal(false)}
                className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2 pr-1 divide-y divide-gray-100 dark:divide-gray-800">
              {allEmployees
                .filter(e => {
                  const empId = e.employee_id || e.id;
                  const alreadyInProj = (selectedProjectForAdd.members || []).some((m: any) => m.id === empId || m.employee_id === empId);
                  return !alreadyInProj;
                })
                .map(e => {
                  const empId = e.employee_id || e.id;
                  const isBench = !e.allocated_project || e.allocated_project.toLowerCase().includes('bench') || e.billability_pct === 0;
                  return (
                    <div key={empId} className="pt-2.5 pb-2 flex items-center justify-between text-xs hover:bg-gray-50/50 dark:hover:bg-gray-800/50 px-2 rounded-xl transition">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white flex items-center justify-center text-[10px] font-bold flex-shrink-0">
                          {e.name?.slice(0, 2).toUpperCase()}
                        </div>
                        <div>
                          <p className="font-semibold text-gray-900 dark:text-white">{e.name}</p>
                          <p className="text-[10px] text-gray-400">
                            {e.role} &bull; {e.department} &bull;{' '}
                            <span className={isBench ? 'text-amber-500 font-bold' : 'text-gray-400'}>
                              {isBench ? 'Available on Bench' : e.allocated_project}
                            </span>
                          </p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleAddMember(selectedProjectForAdd.id, empId)}
                        className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs transition"
                      >
                        Assign
                      </button>
                    </div>
                  );
                })}
            </div>

            <div className="pt-2 border-t border-gray-100 dark:border-gray-800 flex justify-end">
              <button
                type="button"
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 text-gray-700 dark:text-gray-300 rounded-xl text-xs font-semibold transition"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

