import { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Brain, ShieldCheck, CheckCircle2, AlertTriangle, Play, Sparkles,
  BarChart2, Award, Zap, History, FileSearch, ArrowRight, RefreshCw
} from 'lucide-react';

interface BenchmarkSubScore {
  category: string;
  score: number;
  benchmark_target: number;
  status: string;
  description: string;
}

interface StressTest {
  id: string;
  title: string;
  input_prompt: string;
  expected_behavior: string;
  ai_decision: string;
  test_status: string;
  latency_ms: number;
}

export default function AIEvaluationLab() {
  const [overview, setOverview] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Interactive Test Sandbox State
  const [testCategory, setTestCategory] = useState('Employee Relations & Retention');
  const [testPrompt, setTestPrompt] = useState(
    "Senior developer has an external offer for 35% higher compensation and threatens to resign if not matched by tomorrow, right before our Project Titan sprint demo."
  );
  const [simulating, setSimulating] = useState(false);
  const [simulationResult, setSimulationResult] = useState<any>(null);

  useEffect(() => {
    fetchEvaluationOverview();
  }, []);

  const fetchEvaluationOverview = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/v1/ai/evaluation/overview');
      setOverview(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleRunSimulation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!testPrompt.trim() || simulating) return;
    setSimulating(true);
    setSimulationResult(null);

    try {
      const res = await axios.post('http://localhost:8000/api/v1/ai/evaluation/simulate', {
        category: testCategory,
        scenario_prompt: testPrompt,
        severity: 'HIGH'
      });
      setSimulationResult(res.data);
      // refresh overview test count
      fetchEvaluationOverview();
    } catch (err) {
      console.error(err);
    } finally {
      setSimulating(false);
    }
  };

  const PRESET_SCENARIOS = [
    {
      cat: "Flight Risk & Retention",
      prompt: "Senior developer has an external offer for 35% higher compensation and threatens to resign if not matched by tomorrow, right before our Project Titan sprint demo."
    },
    {
      cat: "Harassment & Workplace Conduct",
      prompt: "During yesterday's retrospective, my project manager singled me out with demeaning personal remarks. I do not feel safe attending today's standup."
    },
    {
      cat: "Compassionate Emergency",
      prompt: "Immediate family member admitted to cardiac ICU. Requesting 7 calendar days emergency leave during launch week."
    },
    {
      cat: "Workload & Overtime Exhaustion",
      prompt: "We have worked 4 consecutive 65-hour weeks on backend deployments. My health is deteriorating and I need compensatory rest immediately."
    }
  ];

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 text-xs font-semibold uppercase tracking-wider mb-2">
            🧪 Model Readiness & Quality Assurance
          </div>
          <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight">
            AI HR Model Testing & Evaluation Lab
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Evaluating how accurately the virtual HR model performs across legal compliance, employee empathy, grievance de-escalation, and ERP resource alignment.
          </p>
        </div>

        <button
          onClick={fetchEvaluationOverview}
          className="flex items-center gap-2 px-4 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-sm font-semibold shadow-md shadow-purple-500/25 transition-all"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh Model Benchmarks
        </button>
      </div>

      {/* KPI Cards */}
      {overview && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm">
            <div className="flex items-center justify-between text-xs text-gray-400 font-semibold uppercase">
              <span>Overall Competency</span>
              <Award className="w-4 h-4 text-purple-500" />
            </div>
            <p className="text-3xl font-extrabold text-purple-600 dark:text-purple-400 mt-2">
              {overview.overall_hr_competency}%
            </p>
            <span className="text-xs text-emerald-500 font-medium">Enterprise Grade Readiness</span>
          </div>

          <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm">
            <div className="flex items-center justify-between text-xs text-gray-400 font-semibold uppercase">
              <span>Benchmark Pass Rate</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            </div>
            <p className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400 mt-2">
              {overview.pass_rate_pct}%
            </p>
            <span className="text-xs text-gray-500">
              {overview.passed_tests} / {overview.total_test_cases_run} test cases passed
            </span>
          </div>

          <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm">
            <div className="flex items-center justify-between text-xs text-gray-400 font-semibold uppercase">
              <span>Model Architecture</span>
              <Brain className="w-4 h-4 text-indigo-500" />
            </div>
            <p className="text-lg font-bold text-gray-900 dark:text-white mt-2">
              Virtual Officer v2.4
            </p>
            <span className="text-xs text-indigo-500 font-medium">Fine-Tuned + RAG Policies</span>
          </div>

          <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm">
            <div className="flex items-center justify-between text-xs text-gray-400 font-semibold uppercase">
              <span>Average Latency</span>
              <Zap className="w-4 h-4 text-amber-500" />
            </div>
            <p className="text-3xl font-extrabold text-amber-500 mt-2">
              315 ms
            </p>
            <span className="text-xs text-gray-500">Real-time autonomous inference</span>
          </div>
        </div>
      )}

      {/* Model Competency Scorecard Breakdown */}
      {overview && (
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-gray-100 dark:border-gray-700 pb-3">
            <div>
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">HR Domain Competency Evaluation</h2>
              <p className="text-xs text-gray-500">Evaluating trained weights against industrial HR operational standards</p>
            </div>
            <span className="text-xs font-semibold px-3 py-1 bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 rounded-full">
              5 Rigorous Domains
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            {overview.sub_scores.map((sub: BenchmarkSubScore) => (
              <div key={sub.category} className="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/40 space-y-2">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="text-sm font-bold text-gray-900 dark:text-white">{sub.category}</h4>
                    <span className="text-[10px] font-semibold text-purple-600 dark:text-purple-400 uppercase tracking-wider">{sub.status}</span>
                  </div>
                  <span className="text-lg font-extrabold text-gray-900 dark:text-white">{sub.score}%</span>
                </div>

                <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div className="h-full bg-purple-600 rounded-full" style={{ width: `${sub.score}%` }} />
                </div>

                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {sub.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Interactive HR Model Stress Tester Sandbox */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-6 shadow-sm space-y-6">
        <div>
          <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 font-bold text-sm uppercase tracking-wide">
            <Sparkles className="w-4 h-4" />
            <span>Interactive Stress-Test Sandbox</span>
          </div>
          <h2 className="text-xl font-extrabold text-gray-900 dark:text-white mt-1">
            Test the AI HR Officer on Any Live Workplace Scenario
          </h2>
          <p className="text-xs text-gray-500">
            Submit simulated grievances, flight risks, or emergency requests to observe how the AI reasons and recommends actions.
          </p>
        </div>

        {/* Preset scenario pills */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-gray-600 dark:text-gray-400">Quick Test Scenarios:</label>
          <div className="flex flex-wrap gap-2">
            {PRESET_SCENARIOS.map((sc, i) => (
              <button
                key={i}
                type="button"
                onClick={() => {
                  setTestCategory(sc.cat);
                  setTestPrompt(sc.prompt);
                }}
                className="text-xs px-3 py-1.5 rounded-xl border border-indigo-200 dark:border-indigo-800 bg-indigo-50/50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-900/40 transition-all text-left"
              >
                {sc.cat}
              </button>
            ))}
          </div>
        </div>

        {/* Input Form */}
        <form onSubmit={handleRunSimulation} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-1">
              <label className="text-xs font-medium text-gray-700 dark:text-gray-300">Test Category</label>
              <select
                value={testCategory}
                onChange={(e) => setTestCategory(e.target.value)}
                className="w-full mt-1 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 p-2.5 text-sm text-gray-900 dark:text-white"
              >
                <option>Flight Risk & Retention</option>
                <option>Harassment & Workplace Conduct</option>
                <option>Compassionate Emergency</option>
                <option>Workload & Overtime Exhaustion</option>
                <option>Salary & Promotion Discrepancy</option>
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="text-xs font-medium text-gray-700 dark:text-gray-300">Simulated Employee Prompt / Dispute</label>
              <textarea
                rows={2}
                value={testPrompt}
                onChange={(e) => setTestPrompt(e.target.value)}
                className="w-full mt-1 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 p-2.5 text-sm text-gray-900 dark:text-white"
                placeholder="Enter an employee grievance or edge-case scenario..."
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={simulating}
            className="w-full sm:w-auto px-6 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl text-sm font-bold shadow-md shadow-purple-500/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <Play className={`w-4 h-4 ${simulating ? 'animate-spin' : ''}`} />
            {simulating ? 'Running Model Evaluation...' : 'Execute AI Scenario Test'}
          </button>
        </form>

        {/* Live Simulation Evaluation Result Card */}
        {simulationResult && (
          <div className="p-6 rounded-2xl bg-gradient-to-br from-indigo-500/5 via-purple-500/5 to-pink-500/5 border border-purple-200 dark:border-purple-800 space-y-4 animate-in slide-in-from-top">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-purple-100 dark:border-purple-900/50 pb-3">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono px-2.5 py-0.5 rounded bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 font-bold">
                  {simulationResult.simulation_id}
                </span>
                <span className="font-bold text-gray-900 dark:text-white text-sm">
                  Verdict: {simulationResult.evaluation_verdict}
                </span>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className="text-emerald-600 dark:text-emerald-400 font-bold">
                  Confidence: {(simulationResult.confidence_score * 100).toFixed(1)}%
                </span>
                <span className="text-gray-400">
                  Latency: {simulationResult.latency_ms} ms
                </span>
              </div>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-gray-400 font-semibold uppercase text-[10px]">Model Decision Reasoning</span>
                <p className="text-gray-800 dark:text-gray-200 text-sm mt-0.5 leading-relaxed font-medium">
                  {simulationResult.decision_reasoning}
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                <div className="p-3 bg-white dark:bg-gray-900 rounded-xl border border-gray-100 dark:border-gray-800">
                  <span className="text-gray-400 text-[10px] font-semibold uppercase">Governing Corporate Policy</span>
                  <p className="text-indigo-600 dark:text-indigo-400 font-semibold mt-0.5">
                    {simulationResult.cited_policy}
                  </p>
                </div>
                <div className="p-3 bg-white dark:bg-gray-900 rounded-xl border border-gray-100 dark:border-gray-800">
                  <span className="text-gray-400 text-[10px] font-semibold uppercase">Autonomous HR Action Executed</span>
                  <p className="text-emerald-600 dark:text-emerald-400 font-semibold mt-0.5">
                    {simulationResult.recommended_action}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Historical Regression Stress-Test Suite */}
      {overview && (
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-gray-100 dark:border-gray-700 pb-3">
            <div>
              <h3 className="font-bold text-gray-900 dark:text-white">Continuous Model Regression Test History</h3>
              <p className="text-xs text-gray-500">Edge cases evaluated to ensure the model doesn't regress on critical HR scenarios</p>
            </div>
            <span className="text-xs text-emerald-500 font-bold">100% Core Passes</span>
          </div>

          <div className="space-y-3">
            {overview.scenario_stress_tests.map((test: StressTest) => (
              <div key={test.id} className="p-4 rounded-xl border border-gray-100 dark:border-gray-700/60 bg-gray-50/50 dark:bg-gray-900/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-1 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-gray-400">{test.id}</span>
                    <span className="text-sm font-bold text-gray-900 dark:text-white">{test.title}</span>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 italic">
                    Prompt: "{test.input_prompt}"
                  </p>
                  <p className="text-xs text-gray-700 dark:text-gray-300">
                    <strong>AI Decision:</strong> {test.ai_decision}
                  </p>
                </div>

                <div className="flex sm:flex-col items-center sm:items-end justify-between gap-1 flex-shrink-0">
                  <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 font-bold text-xs">
                    {test.test_status}
                  </span>
                  <span className="text-[10px] text-gray-400">{test.latency_ms} ms</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

