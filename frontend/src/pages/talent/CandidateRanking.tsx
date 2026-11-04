import { useState, useEffect } from 'react';

import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Award, RefreshCw, ChevronDown, ChevronUp, UserCheck, ShieldAlert, Sparkles, X, Bot } from 'lucide-react';


interface CandidateRankingItem {
  rank: number;
  candidate_id: string;
  name: string;
  email: string | null;
  experience: number;
  skills: string[];
  degree: string | null;
  match_score: number;
  matched_skills: string[];
  missing_skills: string[];
  experience_match: string;
  education_match: string;
  semantic_similarity: number;
  explanation: string;
}

interface JobRankingResponse {
  job_id: string;
  job_title: string;
  total_candidates: number;
  rankings: CandidateRankingItem[];
}

export default function CandidateRanking() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [rankingData, setRankingData] = useState<JobRankingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [isRanking, setIsRanking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedCandidate, setExpandedCandidate] = useState<string | null>(null);
  const [explainModal, setExplainModal] = useState<any | null>(null);
  const [explainingCandId, setExplainingCandId] = useState<string | null>(null);

  const handleExplainMatch = async (candidateId: string) => {
    setExplainingCandId(candidateId);
    try {
      const res = await axios.post('http://localhost:8000/api/v1/ai/explain/recruitment', {
        candidate_id: candidateId,
        job_id: jobId
      });
      setExplainModal(res.data);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to generate AI explanation');
    } finally {
      setExplainingCandId(null);
    }
  };

  const fetchRanking = () => {
    if (!jobId) return;
    setLoading(true);
    axios.get(`http://localhost:8000/api/v1/recruitment/jobs/${jobId}/ranking`)
      .then(res => {
        setRankingData(res.data);
        setError(null);
      })
      .catch(err => {
        console.error(err);
        setError('Failed to fetch candidate rankings.');
      })
      .finally(() => setLoading(false));
  };

  const handleRunRanking = async () => {
    if (!jobId || isRanking) return;
    setIsRanking(true);
    try {
      const res = await axios.post(`http://localhost:8000/api/v1/recruitment/jobs/${jobId}/rank`);
      setRankingData(res.data);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError('Failed to compute candidate ranking.');
    } finally {
      setIsRanking(false);
    }
  };

  useEffect(() => {
    fetchRanking();
  }, [jobId]);

  if (loading) {
    return <div className="p-12 text-center text-gray-500">Calculating AI candidate rankings...</div>;
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Back Button */}
      <button
        onClick={() => navigate('/dashboard/talent/jobs')}
        className="inline-flex items-center text-xs font-medium text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 gap-1"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Jobs
      </button>

      {/* Human-in-the-loop Disclaimer Banner */}
      <div className="p-4 bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800 rounded-xl text-xs text-indigo-900 dark:text-indigo-200 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-indigo-600 dark:text-indigo-400 shrink-0 mt-0.5" />
        <div>
          <p className="font-bold text-sm">Human-in-the-Loop Recruiter Assistance</p>
          <p className="mt-0.5 text-indigo-700 dark:text-indigo-300">
            AI-generated ranking is intended to assist recruiters. Final hiring decisions should be made by authorized HR personnel. The system does not automatically reject candidates.
          </p>
        </div>
      </div>

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Award className="w-7 h-7 text-indigo-600 dark:text-indigo-400" />
            AI Candidate Ranking
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Position: <span className="font-bold text-gray-800 dark:text-gray-200">{rankingData?.job_title}</span> ({rankingData?.job_id})
          </p>
        </div>

        <button
          onClick={handleRunRanking}
          disabled={isRanking}
          className="inline-flex items-center justify-center px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold shadow-sm transition-all gap-2 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isRanking ? 'animate-spin' : ''}`} />
          {isRanking ? 'Re-Calculating Scores...' : 'Re-Run AI Matching'}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg text-sm border border-red-200">
          {error}
        </div>
      )}

      {/* Rankings List */}
      {!rankingData || rankingData.rankings.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-12 text-center">
          <UserCheck className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">No candidates matched yet</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 max-w-sm mx-auto">
            Upload candidate resumes to run multi-factor skill and experience matching.
          </p>
          <button
            onClick={() => navigate('/dashboard/talent/candidates/upload')}
            className="mt-5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold inline-flex items-center gap-2"
          >
            Upload Resumes
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {rankingData.rankings.map(item => {
            const isExpanded = expandedCandidate === item.candidate_id;
            return (
              <div
                key={item.candidate_id}
                className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden hover:shadow-md transition-shadow"
              >
                <div className="p-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
                  {/* Rank & Candidate */}
                  <div className="flex items-center gap-4">
                    <div
                      className={`w-12 h-12 rounded-full flex items-center justify-center font-extrabold text-base ${
                        item.rank === 1
                          ? 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border-2 border-amber-300'
                          : item.rank === 2
                          ? 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 border-2 border-gray-300'
                          : item.rank === 3
                          ? 'bg-amber-50 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400 border border-amber-200'
                          : 'bg-gray-50 text-gray-600 dark:bg-gray-800 dark:text-gray-400 border border-gray-200'
                      }`}
                    >
                      #{item.rank}
                    </div>

                    <div>
                      <Link
                        to={`/dashboard/talent/candidates/${item.candidate_id}`}
                        className="text-lg font-bold text-gray-900 dark:text-white hover:text-indigo-600 dark:hover:text-indigo-400"
                      >
                        {item.name}
                      </Link>
                      <div className="flex flex-wrap gap-x-3 text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                        <span>{item.experience > 0 ? `${item.experience} yrs exp` : 'Entry level'}</span>
                        <span>•</span>
                        <span>{item.degree || 'Degree unspecified'}</span>
                      </div>
                    </div>
                  </div>

                  {/* Skills badges */}
                  <div className="flex flex-wrap gap-1.5 max-w-md">
                    {item.matched_skills.map((s, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 text-xs font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 rounded-md inline-flex items-center gap-1"
                      >
                        ✓ {s}
                      </span>
                    ))}
                    {item.missing_skills.map((s, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 text-xs font-semibold bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300 border border-red-200 dark:border-red-800 rounded-md inline-flex items-center gap-1"
                      >
                        ✗ {s} missing
                      </span>
                    ))}
                  </div>

                  {/* Score & Expand */}
                  <div className="flex items-center gap-6 border-t md:border-t-0 pt-4 md:pt-0 border-gray-100 dark:border-gray-700">
                    <div className="text-right">
                      <span className="text-3xl font-extrabold text-indigo-600 dark:text-indigo-400">
                        {Math.round(item.match_score)}%
                      </span>
                      <span className="text-xs text-gray-400 block font-medium">Match Score</span>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleExplainMatch(item.candidate_id)}
                        disabled={explainingCandId === item.candidate_id}
                        className="px-3 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-xl text-xs font-semibold shadow-xs flex items-center gap-1.5 transition-all disabled:opacity-50"
                        title="Generate natural-language Grok match rationale"
                      >
                        <Sparkles className={`w-3.5 h-3.5 ${explainingCandId === item.candidate_id ? 'animate-spin' : ''}`} />
                        {explainingCandId === item.candidate_id ? 'Synthesizing...' : 'Explain Match (Grok)'}
                      </button>

                      <button
                        onClick={() => setExpandedCandidate(isExpanded ? null : item.candidate_id)}
                        className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                      >
                        {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Expanded Explainability Details */}
                {isExpanded && (
                  <div className="px-6 pb-6 pt-4 bg-gray-50 dark:bg-gray-900/60 border-t border-gray-100 dark:border-gray-700 space-y-3">
                    <h4 className="text-xs font-semibold uppercase text-gray-400 tracking-wider">
                      Explainable Ranking Recommendation
                    </h4>

                    <p className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed font-medium">
                      {item.explanation}
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 text-xs">
                      <div className="p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                        <span className="text-gray-400 block">Experience Evaluation</span>
                        <span className="font-semibold text-gray-800 dark:text-gray-200">{item.experience_match}</span>
                      </div>
                      <div className="p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                        <span className="text-gray-400 block">Education Evaluation</span>
                        <span className="font-semibold text-gray-800 dark:text-gray-200">{item.education_match}</span>
                      </div>
                      <div className="p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                        <span className="text-gray-400 block">Semantic Similarity</span>
                        <span className="font-semibold text-gray-800 dark:text-gray-200">{intToPercent(item.semantic_similarity)}% Domain Match</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Grok Match Explanation Modal */}
      {explainModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
          <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-xl w-full border border-gray-100 dark:border-gray-800 shadow-2xl overflow-hidden p-6 space-y-5 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between pb-3 border-b border-gray-100 dark:border-gray-800">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-purple-50 dark:bg-purple-950/50 text-purple-600 dark:text-purple-400 border border-purple-200 dark:border-purple-800">
                  <Bot className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-gray-900 dark:text-white">AI Candidate Match Rationale</h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{explainModal.candidate_name} • {explainModal.job_title}</p>
                </div>
              </div>
              <button
                onClick={() => setExplainModal(null)}
                className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Score pill */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-gray-50 dark:bg-gray-800/60 rounded-xl border border-gray-100 dark:border-gray-800">
                <span className="text-[11px] text-gray-400 block font-medium">Match Score</span>
                <span className="text-2xl font-black text-indigo-600 dark:text-indigo-400">{explainModal.match_score}%</span>
              </div>
              <div className="p-3 bg-gray-50 dark:bg-gray-800/60 rounded-xl border border-gray-100 dark:border-gray-800">
                <span className="text-[11px] text-gray-400 block font-medium">Experience Fit</span>
                <span className="text-sm font-bold text-gray-800 dark:text-gray-200">{explainModal.experience_verdict}</span>
              </div>
            </div>

            {/* Skills */}
            <div className="space-y-2">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Skill Alignment</p>
              <div className="flex flex-wrap gap-1.5">
                {explainModal.matched_skills.map((s: string, i: number) => (
                  <span key={i} className="px-2 py-0.5 text-xs bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 rounded-md border border-emerald-200 dark:border-emerald-800">
                    ✓ {s}
                  </span>
                ))}
                {explainModal.missing_skills.map((s: string, i: number) => (
                  <span key={i} className="px-2 py-0.5 text-xs bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300 rounded-md border border-red-200 dark:border-red-800">
                    ✗ {s} (missing)
                  </span>
                ))}
              </div>
            </div>

            {/* AI Explanation Content */}
            <div className="p-4 bg-indigo-50/50 dark:bg-indigo-950/30 rounded-2xl border border-indigo-100 dark:border-indigo-900/40 space-y-2">
              <div className="flex items-center gap-2 text-indigo-700 dark:text-indigo-300 text-xs font-bold uppercase tracking-wider">
                <Sparkles className="w-3.5 h-3.5" />
                Grok AI Synthesis
              </div>
              <p className="text-xs text-gray-800 dark:text-gray-200 leading-relaxed font-normal whitespace-pre-wrap">
                {explainModal.ai_explanation}
              </p>
            </div>

            {/* Disclaimer */}
            <p className="text-[11px] text-gray-400 dark:text-gray-500 italic">
              * AI-assisted candidate screening summary. Human review required for hiring decisions.
            </p>

            <button
              onClick={() => setExplainModal(null)}
              className="w-full py-2.5 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-xl text-xs font-semibold transition-colors"
            >
              Close Rationale
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function intToPercent(val: number) {
  return Math.round((val || 0) * 100);
}
