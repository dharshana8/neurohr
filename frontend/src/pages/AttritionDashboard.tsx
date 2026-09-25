import { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Legend,
} from 'recharts';
import { Brain, Play, AlertTriangle, Shield, TrendingDown, Users, RefreshCw, Sparkles, X } from 'lucide-react';

interface Summary {
  total_analyzed: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
}

function RiskBadge({ level }: { level: string }) {
  const configs: Record<string, { label: string; classes: string }> = {
    HIGH: { label: 'High Risk', classes: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 border border-red-200 dark:border-red-800' },
    MEDIUM: { label: 'Medium Risk', classes: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 border border-amber-200 dark:border-amber-800' },
    LOW: { label: 'Low Risk', classes: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800' },
  };
  const config = configs[level] ?? configs.LOW;
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${config.classes}`}>
      {config.label}
    </span>
  );
}

function RiskMeter({ prob }: { prob: number }) {
  const pct = Math.round(prob * 100);
  const color = pct >= 70 ? '#ef4444' : pct >= 40 ? '#f59e0b' : '#10b981';
  return (
    <div className="flex items-center gap-2 min-w-[120px]">
      <div className="flex-1 h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <span className="text-xs font-bold tabular-nums" style={{ color }}>{pct}%</span>
    </div>
  );
}

export default function AttritionDashboard() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [highRisk, setHighRisk] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const [explainModal, setExplainModal] = useState<any | null>(null);
  const [explainingEmpId, setExplainingEmpId] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleExplainRisk = async (e: React.MouseEvent, employeeId: string) => {
    e.stopPropagation();
    setExplainingEmpId(employeeId);
    try {
      const res = await axios.post('http://localhost:8000/api/v1/ai/explain/attrition', {
        employee_id: employeeId
      });
      setExplainModal(res.data);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to generate risk explanation');
    } finally {
      setExplainingEmpId(null);
    }
  };

  const fetchData = async () => {
    setIsLoading(true);
    setError('');
    try {
      const [sumRes, hrRes] = await Promise.all([
        axios.get('http://localhost:8000/api/v1/attrition/summary'),
        axios.get('http://localhost:8000/api/v1/attrition/high-risk'),
      ]);
      setSummary(sumRes.data);
      setHighRisk(hrRes.data);
    } catch {
      setError('Unable to load attrition analysis.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleRunAnalysis = async () => {
    setIsAnalyzing(true);
    setError('');
    try {
      await axios.post('http://localhost:8000/api/v1/attrition/predict-all');
      await fetchData();
    } catch {
      setError('Failed to run bulk attrition analysis.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="p-8 max-w-7xl mx-auto space-y-6 page-enter">
        <div className="skeleton h-8 w-64 rounded-xl" />
        <div className="grid grid-cols-4 gap-5">
          {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-28 rounded-2xl" />)}
        </div>
        <div className="skeleton h-80 rounded-2xl" />
      </div>
    );
  }

  if (!summary || summary.total_analyzed === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] p-8 text-center page-enter">
        <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-gradient-to-br from-indigo-500/20 to-purple-500/20 flex items-center justify-center">
          <Brain className="w-12 h-12 text-indigo-500" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">No Attrition Analysis Yet</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md mb-2">
          Run the AI-powered attrition model across your imported workforce to identify retention risks and at-risk employees.
        </p>
        <p className="text-xs text-gray-400 dark:text-gray-500 mb-8">
          Powered by Random Forest Model (demo-v1)
        </p>
        {error && (
          <div className="mb-6 px-4 py-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm rounded-xl">
            {error}
          </div>
        )}
        <button
          onClick={handleRunAnalysis}
          disabled={isAnalyzing}
          className="flex items-center gap-2 px-8 py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-semibold shadow-lg shadow-indigo-500/25 transition-all disabled:opacity-60"
        >
          {isAnalyzing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          {isAnalyzing ? 'Running AI Model...' : 'Run Attrition Analysis'}
        </button>
      </div>
    );
  }

  const pieData = [
    { name: 'High Risk', value: summary.high_risk, color: '#ef4444' },
    { name: 'Medium Risk', value: summary.medium_risk, color: '#f59e0b' },
    { name: 'Low Risk', value: summary.low_risk, color: '#10b981' },
  ];

  const barData = [
    { name: 'High', value: summary.high_risk, fill: '#ef4444' },
    { name: 'Medium', value: summary.medium_risk, fill: '#f59e0b' },
    { name: 'Low', value: summary.low_risk, fill: '#10b981' },
  ];

  const retentionRate = summary.total_analyzed > 0
    ? Math.round(((summary.total_analyzed - summary.high_risk) / summary.total_analyzed) * 100)
    : 0;

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-8 page-enter">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="p-2 bg-indigo-50 dark:bg-indigo-900/30 rounded-xl">
              <Brain className="w-5 h-5 text-indigo-500" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Attrition Intelligence</h2>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 ml-12">
            AI-powered retention risk analysis — Random Forest Model
          </p>
        </div>
        <button
          onClick={handleRunAnalysis}
          disabled={isAnalyzing}
          className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-semibold shadow-md shadow-indigo-500/20 transition-all disabled:opacity-60"
        >
          {isAnalyzing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          {isAnalyzing ? 'Analyzing...' : 'Re-run Analysis'}
        </button>
      </div>

      {error && (
        <div className="px-4 py-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm rounded-xl">
          {error}
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        {[
          {
            label: 'Total Analyzed',
            value: summary.total_analyzed,
            icon: <Users className="w-5 h-5 text-indigo-500" />,
            bg: 'bg-indigo-50 dark:bg-indigo-900/20',
            textColor: 'text-gray-900 dark:text-white',
          },
          {
            label: 'High Risk',
            value: summary.high_risk,
            icon: <AlertTriangle className="w-5 h-5 text-red-500" />,
            bg: 'bg-red-50 dark:bg-red-900/20',
            textColor: 'text-red-600 dark:text-red-400',
          },
          {
            label: 'Medium Risk',
            value: summary.medium_risk,
            icon: <TrendingDown className="w-5 h-5 text-amber-500" />,
            bg: 'bg-amber-50 dark:bg-amber-900/20',
            textColor: 'text-amber-600 dark:text-amber-400',
          },
          {
            label: 'Retention Rate',
            value: `${retentionRate}%`,
            icon: <Shield className="w-5 h-5 text-emerald-500" />,
            bg: 'bg-emerald-50 dark:bg-emerald-900/20',
            textColor: 'text-emerald-600 dark:text-emerald-400',
          },
        ].map(card => (
          <div
            key={card.label}
            className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-100 dark:border-gray-700 shadow-sm card-hover"
          >
            <div className={`p-2.5 rounded-xl w-fit ${card.bg} mb-3`}>{card.icon}</div>
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">{card.label}</p>
            <p className={`text-3xl font-bold ${card.textColor}`}>{card.value}</p>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Donut */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-6">
          <h3 className="text-base font-bold text-gray-900 dark:text-white mb-1">Risk Distribution</h3>
          <p className="text-xs text-gray-400 mb-4">Breakdown across risk levels</p>
          <div className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={80} paddingAngle={4} dataKey="value">
                  {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                </Pie>
                <Tooltip contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 12, color: '#f8fafc', fontSize: 12 }} />
                <Legend formatter={(v: any) => <span className="text-xs text-gray-600 dark:text-gray-300">{v}</span>} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Bar chart */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-6">
          <h3 className="text-base font-bold text-gray-900 dark:text-white mb-1">Risk Levels</h3>
          <p className="text-xs text-gray-400 mb-4">Employee count by risk category</p>
          <div className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData} barSize={40}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 12, color: '#f8fafc', fontSize: 12 }} />
                <Bar dataKey="value" name="Employees" radius={[8, 8, 0, 0]}>
                  {barData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk summary text */}
        <div className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-2xl p-6 text-white shadow-xl shadow-indigo-500/20">
          <div className="p-2.5 bg-white/20 rounded-xl w-fit mb-4">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <h3 className="text-base font-bold mb-1">AI Insights</h3>
          <p className="text-indigo-100 text-xs mb-4">Based on the current analysis</p>
          <div className="space-y-3">
            <div className="bg-white/10 rounded-xl p-3">
              <p className="text-xs font-semibold text-white">{summary.high_risk} employees</p>
              <p className="text-xs text-indigo-200 mt-0.5">at high risk of leaving in 6 months</p>
            </div>
            <div className="bg-white/10 rounded-xl p-3">
              <p className="text-xs font-semibold text-white">{retentionRate}% retention rate</p>
              <p className="text-xs text-indigo-200 mt-0.5">workforce likely to stay</p>
            </div>
            <div className="bg-white/10 rounded-xl p-3">
              <p className="text-xs font-semibold text-white">{summary.low_risk} low-risk</p>
              <p className="text-xs text-indigo-200 mt-0.5">employees showing high engagement</p>
            </div>
          </div>
        </div>
      </div>

      {/* High Risk Table */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm overflow-hidden">
        <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-gray-900 dark:text-white">High Risk Employees</h3>
            <p className="text-xs text-gray-400 mt-0.5">{highRisk.length} employees flagged for immediate attention</p>
          </div>
          <span className="px-3 py-1 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-xs font-bold rounded-full border border-red-200 dark:border-red-800">
            {highRisk.length} at risk
          </span>
        </div>

        {highRisk.length === 0 ? (
          <div className="p-12 text-center">
            <Shield className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
            <p className="text-sm font-semibold text-gray-700 dark:text-gray-200">Great news — no high risk employees!</p>
            <p className="text-xs text-gray-400 mt-1">Your workforce shows strong retention signals.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-700/50">
                <tr>
                  <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Employee</th>
                  <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Department</th>
                  <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Role</th>
                  <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Risk Level</th>
                  <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Probability</th>
                  <th className="px-6 py-3.5 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">AI Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {highRisk.map((emp) => (
                  <tr
                    key={emp.employee_id}
                    className="hover:bg-red-50/30 dark:hover:bg-red-900/10 cursor-pointer transition-colors"
                    onClick={() => navigate(`/dashboard/workforce/employees/${emp.employee_id}`)}
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-red-400 to-red-600 flex items-center justify-center flex-shrink-0">
                          <span className="text-white text-xs font-bold">
                            {emp.name?.slice(0, 2).toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <p className="font-semibold text-gray-900 dark:text-white">{emp.name}</p>
                          <p className="text-xs text-gray-400">{emp.employee_id}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-gray-600 dark:text-gray-300">{emp.department}</td>
                    <td className="px-6 py-4 text-gray-500 dark:text-gray-400">{emp.role}</td>
                    <td className="px-6 py-4"><RiskBadge level="HIGH" /></td>
                    <td className="px-6 py-4"><RiskMeter prob={emp.probability} /></td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={(e) => handleExplainRisk(e, emp.employee_id)}
                        disabled={explainingEmpId === emp.employee_id}
                        className="px-3 py-1.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs inline-flex items-center gap-1.5 transition-all disabled:opacity-50"
                        title="Explain attrition drivers with Grok AI"
                      >
                        <Sparkles className={`w-3.5 h-3.5 ${explainingEmpId === emp.employee_id ? 'animate-spin' : ''}`} />
                        {explainingEmpId === emp.employee_id ? 'Analyzing...' : 'Explain Risk'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Grok Attrition Explanation Modal */}
      {explainModal && (() => {
        const turnoverProb = typeof explainModal.probability === 'number'
          ? explainModal.probability
          : typeof explainModal.risk_score === 'number'
          ? explainModal.risk_score
          : 0;

        const topRisk = (explainModal.top_risk_factors && explainModal.top_risk_factors.length > 0)
          ? explainModal.top_risk_factors
          : (explainModal.model_factors || [])
              .filter((f: any) => f.impact === 'negative' || (typeof f.shap_value === 'number' && f.shap_value > 0))
              .map((f: any) => ({
                factor: f.feature ? f.feature.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase()) : (f.factor || 'Risk Driver'),
                impact: f.shap_value !== undefined ? (typeof f.shap_value === 'number' ? Math.abs(f.shap_value).toFixed(2) : f.shap_value) : (f.impact || 'High')
              }));

        const protective = (explainModal.protective_factors && explainModal.protective_factors.length > 0)
          ? explainModal.protective_factors
          : (explainModal.model_factors || [])
              .filter((f: any) => f.impact === 'positive' || (typeof f.shap_value === 'number' && f.shap_value <= 0))
              .map((f: any) => ({
                factor: f.feature ? f.feature.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase()) : (f.factor || 'Retention Buffer'),
                impact: f.shap_value !== undefined ? (typeof f.shap_value === 'number' ? Math.abs(f.shap_value).toFixed(2) : f.shap_value) : (f.impact || 'Low')
              }));

        const narrative = explainModal.ai_narrative || explainModal.ai_explanation || 'Detailed attrition analysis generated from model factors.';

        return (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
            <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-xl w-full border border-gray-100 dark:border-gray-800 shadow-2xl overflow-hidden p-6 space-y-5 animate-in fade-in zoom-in-95 duration-200">
              <div className="flex items-center justify-between pb-3 border-b border-gray-100 dark:border-gray-800">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-xl bg-red-50 dark:bg-red-950/50 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800">
                    <Brain className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-gray-900 dark:text-white">Attrition Risk Diagnosis</h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Employee ID: {explainModal.employee_id} • Risk: {explainModal.risk_level || 'ELEVATED'}</p>
                  </div>
                </div>
                <button
                  onClick={() => setExplainModal(null)}
                  className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Probability pill */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-gray-50 dark:bg-gray-800/60 rounded-xl border border-gray-100 dark:border-gray-800">
                  <span className="text-[11px] text-gray-400 block font-medium">Turnover Likelihood</span>
                  <span className="text-2xl font-black text-red-600 dark:text-red-400">{Math.round(turnoverProb * 100)}%</span>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-800/60 rounded-xl border border-gray-100 dark:border-gray-800">
                  <span className="text-[11px] text-gray-400 block font-medium">Risk Classification</span>
                  <span className="text-sm font-bold text-red-600 dark:text-red-400">{explainModal.risk_level || 'HIGH'} ATTENTION</span>
                </div>
              </div>

              {/* SHAP Factor Pills */}
              <div className="space-y-2">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Top Predictive Drivers (SHAP)</p>
                <div className="space-y-1.5">
                  {topRisk.map((f: any, idx: number) => {
                    const impactStr = String(f.impact).startsWith('+') || String(f.impact).startsWith('-') ? String(f.impact) : `+${f.impact}`;
                    return (
                      <div key={idx} className="flex items-center justify-between p-2 rounded-lg bg-red-50/60 dark:bg-red-950/30 border border-red-100 dark:border-red-900/40 text-xs">
                        <span className="font-semibold text-red-800 dark:text-red-300">↑ {f.factor}</span>
                        <span className="font-mono text-red-600 dark:text-red-400 font-bold">{impactStr} risk impact</span>
                      </div>
                    );
                  })}
                  {protective.map((f: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between p-2 rounded-lg bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-100 dark:border-emerald-900/40 text-xs">
                      <span className="font-semibold text-emerald-800 dark:text-emerald-300">↓ {f.factor}</span>
                      <span className="font-mono text-emerald-600 dark:text-emerald-400 font-bold">{f.impact} retention buffer</span>
                    </div>
                  ))}
                  {topRisk.length === 0 && protective.length === 0 && (
                    <p className="text-xs text-gray-400 italic p-2 bg-gray-50 dark:bg-gray-800/40 rounded-lg">
                      No specific factor breakdown available for this employee profile.
                    </p>
                  )}
                </div>
              </div>

              {/* Grok Narrative */}
              <div className="p-4 bg-purple-50/50 dark:bg-purple-950/30 rounded-2xl border border-purple-100 dark:border-purple-900/40 space-y-2">
                <div className="flex items-center gap-2 text-purple-700 dark:text-purple-300 text-xs font-bold uppercase tracking-wider">
                  <Sparkles className="w-3.5 h-3.5" />
                  Grok AI Retention Narrative
                </div>
                <p className="text-xs text-gray-800 dark:text-gray-200 leading-relaxed font-normal whitespace-pre-wrap">
                  {narrative}
                </p>
              </div>

              {/* Disclaimer */}
              <p className="text-[11px] text-gray-400 dark:text-gray-500 italic">
                {explainModal.disclaimer || "* AI-assisted retention intelligence. Requires managerial context and human review."}
              </p>

              <button
                onClick={() => setExplainModal(null)}
                className="w-full py-2.5 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-xl text-xs font-semibold transition-colors"
              >
                Dismiss Diagnosis
              </button>
            </div>
          </div>
        );
      })()}
    </div>
  );
}
