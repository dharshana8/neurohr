import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';
import {
  ArrowLeft, Smile, Meh, Frown,
  RefreshCw, ShieldCheck
} from 'lucide-react';

interface SentimentResult {
  sentiment_id: string;
  feedback_id: string;
  employee_id?: string;
  sentiment: string;
  sentiment_score: {
    positive: number;
    neutral: number;
    negative: number;
    compound: number;
  };
  model_name: string;
  model_version: string;
  analyzed_at: string;
}

interface FeedbackDetail {
  id: string;
  feedback_id: string;
  employee_id?: string;
  department: string;
  category: string;
  feedback_text: string;
  source: string;
  submitted_at: string;
  is_synthetic: boolean;
  sentiment_result?: SentimentResult;
  created_at: string;
  updated_at: string;
}

export default function SentimentDetail() {
  const { feedbackId } = useParams<{ feedbackId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [feedback, setFeedback] = useState<FeedbackDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canViewEmployee = user?.role === 'ORGANIZATION_ADMIN' || user?.role === 'HR_MANAGER';

  useEffect(() => {
    if (feedbackId) {
      fetchDetail();
    }
  }, [feedbackId]);

  const fetchDetail = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get(`/feedback/${feedbackId}`);
      setFeedback(res.data);
    } catch (err: any) {
      console.error('Failed to load feedback details', err);
      setError(err.response?.data?.detail || 'Feedback not found');
    } finally {
      setLoading(false);
    }
  };

  const handleReanalyze = async () => {
    if (!feedbackId) return;
    setAnalyzing(true);
    try {
      await api.post(`/sentiment/analyze/${feedbackId}`);
      await fetchDetail();
    } catch (err) {
      console.error('Re-analysis failed', err);
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24 text-slate-400">
        <RefreshCw className="w-6 h-6 animate-spin text-indigo-400 mr-3" />
        <span>Loading feedback sentiment breakdown...</span>
      </div>
    );
  }

  if (error || !feedback) {
    return (
      <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-12 text-center max-w-md mx-auto space-y-4">
        <h3 className="text-base font-bold text-white">Record Not Found</h3>
        <p className="text-xs text-slate-400">{error || 'The requested feedback record does not exist or has been removed.'}</p>
        <button
          onClick={() => navigate('/dashboard/intelligence/sentiment/feedback')}
          className="px-4 py-2 text-xs font-semibold text-white bg-indigo-600 rounded-lg"
        >
          Back to Feedback List
        </button>
      </div>
    );
  }

  const res = feedback.sentiment_result;
  const score = res?.sentiment_score;

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Top Navigation */}
      <button
        onClick={() => navigate('/dashboard/intelligence/sentiment/feedback')}
        className="flex items-center gap-1.5 text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition"
      >
        <ArrowLeft className="w-3.5 h-3.5" /> Back to Feedback Hub
      </button>

      {/* Header Card */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs px-2.5 py-0.5 rounded-md bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-semibold">
                {feedback.category}
              </span>
              <span className="text-xs text-slate-400">• {feedback.source}</span>
              {feedback.is_synthetic && (
                <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  Synthetic Demo
                </span>
              )}
            </div>
            <h1 className="text-xl font-bold text-white">
              {feedback.department} Department Feedback
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleReanalyze}
              disabled={analyzing}
              className="px-3.5 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg shadow-lg shadow-indigo-500/20 transition flex items-center gap-2"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${analyzing ? 'animate-spin' : ''}`} />
              {analyzing ? 'Re-analyzing...' : 'Re-Analyze'}
            </button>
          </div>
        </div>

        {/* Feedback Content */}
        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 text-sm text-slate-200 leading-relaxed">
          "{feedback.feedback_text}"
        </div>

        {/* Metadata Footer */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs text-slate-400 pt-2 border-t border-slate-800/60">
          <div>
            <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Submitted Date</div>
            <div className="text-slate-200 mt-0.5">{new Date(feedback.submitted_at).toLocaleDateString()}</div>
          </div>

          <div>
            <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Source Channel</div>
            <div className="text-slate-200 mt-0.5">{feedback.source}</div>
          </div>

          <div>
            <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Department</div>
            <div className="text-slate-200 mt-0.5">{feedback.department}</div>
          </div>

          <div>
            <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Employee Identity</div>
            <div className="text-slate-200 mt-0.5 flex items-center gap-1">
              {canViewEmployee && feedback.employee_id ? (
                <span>{feedback.employee_id}</span>
              ) : (
                <span className="text-slate-500 italic flex items-center gap-1 text-[11px]">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  Protected / Anonymized
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Sentiment Analysis Breakdown */}
      {res ? (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
            <div>
              <h3 className="text-base font-bold text-white">Sentiment Analysis Breakdown</h3>
              <p className="text-xs text-slate-400">
                Processed via deterministic NLP model ({res.model_name} v{res.model_version})
              </p>
            </div>

            <div>
              {res.sentiment === 'POSITIVE' && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <Smile className="w-4 h-4" /> POSITIVE SENTIMENT
                </span>
              )}
              {res.sentiment === 'NEUTRAL' && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  <Meh className="w-4 h-4" /> NEUTRAL SENTIMENT
                </span>
              )}
              {res.sentiment === 'NEGATIVE' && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  <Frown className="w-4 h-4" /> NEGATIVE SENTIMENT
                </span>
              )}
            </div>
          </div>

          {/* Metric Cards */}
          {score && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 text-center">
                <div className="text-xs text-slate-400 font-semibold mb-1">Compound Score</div>
                <div className="text-xl font-black text-indigo-400">{score.compound}</div>
                <div className="text-[10px] text-slate-500 mt-1">Range: -1.0 to +1.0</div>
              </div>

              <div className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/20 text-center">
                <div className="text-xs text-emerald-400 font-semibold mb-1">Positive Valence</div>
                <div className="text-xl font-black text-emerald-400">{score.positive}</div>
                <div className="text-[10px] text-slate-500 mt-1">Normalized proportion</div>
              </div>

              <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/20 text-center">
                <div className="text-xs text-amber-400 font-semibold mb-1">Neutral Proportion</div>
                <div className="text-xl font-black text-amber-400">{score.neutral}</div>
                <div className="text-[10px] text-slate-500 mt-1">Normalized proportion</div>
              </div>

              <div className="p-4 rounded-xl bg-rose-500/5 border border-rose-500/20 text-center">
                <div className="text-xs text-rose-400 font-semibold mb-1">Negative Valence</div>
                <div className="text-xl font-black text-rose-400">{score.negative}</div>
                <div className="text-[10px] text-slate-500 mt-1">Normalized proportion</div>
              </div>
            </div>
          )}

          {/* Model Attribution */}
          <div className="flex items-center justify-between text-xs text-slate-500 pt-2">
            <span>Analyzed at: {new Date(res.analyzed_at).toLocaleString()}</span>
            <span>Sentiment ID: {res.sentiment_id.slice(0, 8)}...</span>
          </div>
        </div>
      ) : (
        <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-8 text-center space-y-3">
          <p className="text-xs text-slate-400">This feedback record has not been analyzed yet.</p>
          <button
            onClick={handleReanalyze}
            disabled={analyzing}
            className="px-4 py-2 text-xs font-semibold text-white bg-indigo-600 rounded-lg shadow-lg shadow-indigo-500/20"
          >
            Analyze Now
          </button>
        </div>
      )}
    </div>
  );
}
