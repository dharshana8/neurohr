import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../lib/api';
import {
  Smile, Meh, Frown, Sparkles, TrendingUp,
  Building2, MessageSquare, Tag, RefreshCw,
  Upload, Filter
} from 'lucide-react';
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis,
  CartesianGrid, Tooltip
} from 'recharts';

interface DepartmentItem {
  department: string;
  total_feedback: number;
  positive_count: number;
  neutral_count: number;
  negative_count: number;
  positive_pct: number;
  neutral_pct: number;
  negative_pct: number;
}

interface TrendPoint {
  period: string;
  positive_pct: number;
  neutral_pct: number;
  negative_pct: number;
  total_count: number;
}

interface ThemeItem {
  theme: string;
  count: number;
  percentage: number;
  positive_count: number;
  neutral_count: number;
  negative_count: number;
}

interface AIInsight {
  insight: string;
  overall_sentiment: {
    positive: number;
    neutral: number;
    negative: number;
    total: number;
  };
  top_themes: string[];
  department_summary?: { active_departments: number };
  generated_at: string;
  is_ai_assisted: boolean;
  model: string;
}

export default function WorkplaceSentimentDashboard() {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [analyzingBatch, setAnalyzingBatch] = useState(false);
  const [generatingInsight, setGeneratingInsight] = useState(false);

  // Analytics data
  const [departments, setDepartments] = useState<DepartmentItem[]>([]);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [themes, setThemes] = useState<ThemeItem[]>([]);
  const [totalFeedback, setTotalFeedback] = useState<number>(0);
  const [aiInsight, setAiInsight] = useState<AIInsight | null>(null);

  // Filters
  const [selectedDept, setSelectedDept] = useState<string>('ALL');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');

  useEffect(() => {
    fetchDashboardData();
  }, [selectedDept, selectedCategory]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [deptRes, trendRes, themeRes] = await Promise.all([
        api.get('/sentiment/department'),
        api.get(`/sentiment/trends?department=${selectedDept}&category=${selectedCategory}`),
        api.get(`/sentiment/themes?department=${selectedDept}`)
      ]);

      setDepartments(deptRes.data.departments || []);
      setTotalFeedback(deptRes.data.total_feedback || 0);
      setTrends(trendRes.data.trends || []);
      setThemes(themeRes.data.themes || []);
    } catch (err) {
      console.error('Failed to load sentiment dashboard metrics', err);
    } finally {
      setLoading(false);
    }
  };

  const handleBatchAnalyze = async () => {
    setAnalyzingBatch(true);
    try {
      await api.post('/sentiment/analyze-all?force=true');
      await fetchDashboardData();
    } catch (err) {
      console.error('Batch analysis failed', err);
    } finally {
      setAnalyzingBatch(false);
    }
  };

  const handleGenerateAIInsight = async () => {
    setGeneratingInsight(true);
    try {
      const res = await api.post('/sentiment/insight', {
        department: selectedDept !== 'ALL' ? selectedDept : null
      });
      setAiInsight(res.data);
    } catch (err) {
      console.error('Failed to generate AI executive insight', err);
    } finally {
      setGeneratingInsight(false);
    }
  };

  // Compute overall totals from departments
  const totalPositive = departments.reduce((acc, d) => acc + d.positive_count, 0);
  const totalNeutral = departments.reduce((acc, d) => acc + d.neutral_count, 0);
  const totalNegative = departments.reduce((acc, d) => acc + d.negative_count, 0);

  const overallPositivePct = totalFeedback > 0 ? Math.round((totalPositive / totalFeedback) * 100) : 0;
  const overallNeutralPct = totalFeedback > 0 ? Math.round((totalNeutral / totalFeedback) * 100) : 0;
  const overallNegativePct = totalFeedback > 0 ? Math.round((totalNegative / totalFeedback) * 100) : 0;

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <Smile className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Workplace Sentiment Intelligence</h1>
              <p className="text-sm text-slate-400">
                Ethical, authorized employee sentiment analytics and thematic intelligence
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center flex-wrap gap-3">
          <button
            onClick={() => navigate('/dashboard/intelligence/sentiment/feedback')}
            className="px-4 py-2 text-sm font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 transition flex items-center gap-2"
          >
            <MessageSquare className="w-4 h-4 text-slate-400" />
            Manage Feedback
          </button>

          <button
            onClick={handleBatchAnalyze}
            disabled={analyzingBatch || totalFeedback === 0}
            className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg shadow-lg shadow-indigo-500/20 transition flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${analyzingBatch ? 'animate-spin' : ''}`} />
            {analyzingBatch ? 'Analyzing...' : 'Batch Analyze'}
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-slate-900/60 backdrop-blur-sm border border-slate-800 p-4 rounded-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-400">
          <Filter className="w-4 h-4 text-indigo-400" />
          <span>Filters:</span>
        </div>

        <div className="flex items-center flex-wrap gap-3">
          {/* Department Filter */}
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Department:</label>
            <select
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value)}
              className="bg-slate-800 text-slate-200 border border-slate-700 rounded-lg px-3 py-1.5 text-xs focus:ring-1 focus:ring-indigo-500 focus:outline-none"
            >
              <option value="ALL">All Departments</option>
              {departments.map((d) => (
                <option key={d.department} value={d.department}>
                  {d.department} ({d.total_feedback})
                </option>
              ))}
            </select>
          </div>

          {/* Category Filter */}
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Category:</label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
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
              <option value="EXIT">Exit Feedback</option>
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20 text-slate-400">
          <RefreshCw className="w-6 h-6 animate-spin text-indigo-400 mr-3" />
          <span>Loading sentiment intelligence metrics...</span>
        </div>
      ) : totalFeedback === 0 ? (
        /* Empty State */
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-12 text-center max-w-2xl mx-auto space-y-4">
          <div className="w-16 h-16 bg-slate-800 rounded-2xl flex items-center justify-center mx-auto text-slate-500">
            <MessageSquare className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-bold text-white">No Sentiment Data Available</h2>
          <p className="text-sm text-slate-400 leading-relaxed">
            No employee feedback has been submitted or imported for this organization yet.
            Upload an authorized feedback CSV or add entries to initiate sentiment scoring.
          </p>
          <div className="pt-2 flex justify-center gap-4">
            <button
              onClick={() => navigate('/dashboard/intelligence/sentiment/feedback')}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg shadow-lg shadow-indigo-500/20 transition flex items-center gap-2"
            >
              <Upload className="w-4 h-4" />
              Import Feedback
            </button>
          </div>
        </div>
      ) : (
        <>
          {/* Top Row: Overall Sentiment & Distribution */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Overall Sentiment Stats */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 relative overflow-hidden">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Overall Sentiment</span>
                <span className="text-xs px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 font-medium border border-slate-700">
                  {totalFeedback} Responses
                </span>
              </div>

              <div className="grid grid-cols-3 gap-3 my-6">
                <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-center">
                  <Smile className="w-6 h-6 text-emerald-400 mx-auto mb-1.5" />
                  <div className="text-2xl font-black text-white">{overallPositivePct}%</div>
                  <div className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">Positive</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">{totalPositive} items</div>
                </div>

                <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-center">
                  <Meh className="w-6 h-6 text-amber-400 mx-auto mb-1.5" />
                  <div className="text-2xl font-black text-white">{overallNeutralPct}%</div>
                  <div className="text-[11px] font-semibold text-amber-400 uppercase tracking-wider">Neutral</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">{totalNeutral} items</div>
                </div>

                <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-center">
                  <Frown className="w-6 h-6 text-rose-400 mx-auto mb-1.5" />
                  <div className="text-2xl font-black text-white">{overallNegativePct}%</div>
                  <div className="text-[11px] font-semibold text-rose-400 uppercase tracking-wider">Negative</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">{totalNegative} items</div>
                </div>
              </div>

              {/* Progress Stack */}
              <div className="space-y-1.5">
                <div className="h-3 w-full bg-slate-800 rounded-full overflow-hidden flex">
                  <div style={{ width: `${overallPositivePct}%` }} className="bg-emerald-500 h-full transition-all duration-500" />
                  <div style={{ width: `${overallNeutralPct}%` }} className="bg-amber-500 h-full transition-all duration-500" />
                  <div style={{ width: `${overallNegativePct}%` }} className="bg-rose-500 h-full transition-all duration-500" />
                </div>
                <div className="flex justify-between text-[11px] text-slate-500 font-medium">
                  <span>VADER Lexicon NLP</span>
                  <span>Model v3.3.2</span>
                </div>
              </div>
            </div>

            {/* AI Executive Insight Card */}
            <div className="lg:col-span-2 bg-gradient-to-br from-slate-900/90 via-purple-950/20 to-slate-900/90 border border-purple-900/30 rounded-2xl p-6 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-purple-400" />
                    <h3 className="text-sm font-bold uppercase tracking-wider text-purple-300">
                      Grok AI Executive Insight
                    </h3>
                  </div>
                  <button
                    onClick={handleGenerateAIInsight}
                    disabled={generatingInsight}
                    className="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-purple-200 bg-purple-900/40 hover:bg-purple-800/60 border border-purple-700/50 transition flex items-center gap-1.5"
                  >
                    <Sparkles className={`w-3.5 h-3.5 ${generatingInsight ? 'animate-spin' : ''}`} />
                    {generatingInsight ? 'Generating...' : 'Generate AI Insight'}
                  </button>
                </div>

                <div className="bg-slate-950/50 border border-purple-900/20 rounded-xl p-4 my-2 text-slate-200 text-sm leading-relaxed min-h-[90px] flex items-center">
                  {aiInsight ? (
                    <p className="italic">"{aiInsight.insight}"</p>
                  ) : (
                    <p className="text-slate-500 italic">
                      Click "Generate AI Insight" to have Grok analyze aggregated sentiment distribution, top themes, and departmental trends without exposing employee PII.
                    </p>
                  )}
                </div>
              </div>

              {aiInsight && (
                <div className="flex items-center justify-between text-xs text-slate-400 pt-3 border-t border-purple-900/20">
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                    Generated via {aiInsight.model}
                  </span>
                  <span>{new Date(aiInsight.generated_at).toLocaleTimeString()}</span>
                </div>
              )}
            </div>
          </div>

          {/* Department Sentiment Breakdown */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2.5">
                <Building2 className="w-5 h-5 text-indigo-400" />
                <h3 className="text-base font-bold text-white">Department Sentiment Breakdown</h3>
              </div>
              <span className="text-xs text-slate-400">Aggregated from stored MongoDB feedback records</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {departments.map((dept) => (
                <div
                  key={dept.department}
                  className="p-4 rounded-xl bg-slate-950/50 border border-slate-800 hover:border-slate-700 transition"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-white text-sm">{dept.department}</h4>
                    <span className="text-xs text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded">
                      {dept.total_feedback} feedback
                    </span>
                  </div>

                  <div className="space-y-2 my-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-emerald-400 font-medium flex items-center gap-1">
                        <Smile className="w-3.5 h-3.5" /> {dept.positive_pct}% Positive
                      </span>
                      <span className="text-rose-400 font-medium flex items-center gap-1">
                        <Frown className="w-3.5 h-3.5" /> {dept.negative_pct}% Negative
                      </span>
                    </div>

                    <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden flex">
                      <div style={{ width: `${dept.positive_pct}%` }} className="bg-emerald-500 h-full" />
                      <div style={{ width: `${dept.neutral_pct}%` }} className="bg-amber-500 h-full" />
                      <div style={{ width: `${dept.negative_pct}%` }} className="bg-rose-500 h-full" />
                    </div>
                  </div>

                  <div className="flex justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800/50">
                    <span>Pos: {dept.positive_count}</span>
                    <span>Neu: {dept.neutral_count}</span>
                    <span>Neg: {dept.negative_count}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Trends & Themes Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Sentiment Trend Over Time */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-indigo-400" />
                  <h3 className="text-base font-bold text-white">Sentiment Trend Over Time</h3>
                </div>
                <span className="text-xs text-slate-400">Monthly Aggregations</span>
              </div>

              {trends.length === 0 ? (
                <div className="text-center py-12 text-slate-500 text-sm">
                  No time-series points available for selected filters.
                </div>
              ) : (
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="posGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="negGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.4} />
                          <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                      <XAxis dataKey="period" stroke="#64748b" fontSize={11} />
                      <YAxis stroke="#64748b" fontSize={11} domain={[0, 100]} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                        labelStyle={{ color: '#cbd5e1', fontWeight: 600 }}
                      />
                      <Area type="monotone" dataKey="positive_pct" name="Positive %" stroke="#10b981" fillOpacity={1} fill="url(#posGrad)" />
                      <Area type="monotone" dataKey="negative_pct" name="Negative %" stroke="#f43f5e" fillOpacity={1} fill="url(#negGrad)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

            {/* Extracted Common Themes */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <Tag className="w-5 h-5 text-indigo-400" />
                  <h3 className="text-base font-bold text-white">Top Workplace Themes</h3>
                </div>
                <span className="text-xs text-slate-400">NLP Topic Extraction</span>
              </div>

              {themes.length === 0 ? (
                <div className="text-center py-12 text-slate-500 text-sm">
                  No themes identified for the current selection.
                </div>
              ) : (
                <div className="space-y-3 max-h-64 overflow-y-auto pr-1">
                  {themes.map((theme, idx) => (
                    <div
                      key={theme.theme}
                      className="p-3 rounded-xl bg-slate-950/40 border border-slate-800/80 flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <span className="w-6 h-6 rounded-lg bg-indigo-500/10 text-indigo-400 font-bold text-xs flex items-center justify-center">
                          {idx + 1}
                        </span>
                        <div>
                          <div className="text-sm font-semibold text-white">{theme.theme}</div>
                          <div className="text-[11px] text-slate-400">
                            {theme.count} mentions ({theme.percentage}% of feedback)
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                          +{theme.positive_count}
                        </span>
                        <span className="text-xs px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20 font-medium">
                          -{theme.negative_count}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
